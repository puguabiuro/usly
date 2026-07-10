(function () {
  const PRODUCT_IDS = {
    user: {
      plus: "usly_user_plus:monthly",
      premium: "usly_user_premium:monthly",
      vip: "usly_user_vip:monthly",
    },
    partner: {
      pro: "usly_partner_pro:monthly",
      premium: "usly_partner_premium:monthly",
    },
  };

  const REVENUECAT_PUBLIC_SDK_KEYS = {
    ios: "",
    android: "",
  };

  let configurePromise = null;
  let configuredAppUserId = null;

  function getProductId(role, plan) {
    return PRODUCT_IDS[String(role || "").toLowerCase()]?.[String(plan || "").toLowerCase()] || null;
  }

  function getPlatform() {
    const platform = window.Capacitor?.getPlatform?.();
    if (platform === "ios" || platform === "android") return platform;
    return "web";
  }

  function getAppUserId(role) {
    const id = window.App?.currentUserId;
    if (!id) return null;

    const normalizedRole = String(role || window.App?.role || "").toLowerCase();
    if (normalizedRole === "partner") return `usly_partner_${id}`;
    return `usly_user_${id}`;
  }

  function getNativePurchasesPlugin() {
    return window.Capacitor?.Plugins?.Purchases || null;
  }

  function getBillingErrorCode(err) {
    return String(
      err?.code ||
      err?.errorCode ||
      err?.userInfo?.readableErrorCode ||
      err?.message ||
      ""
    );
  }

  function isUserCancelledError(err) {
    const code = getBillingErrorCode(err).toLowerCase();
    return !!err?.userCancelled || code.includes("cancel") || code.includes("user_cancelled");
  }

  function getBillingErrorMessageKey(err) {
    const code = getBillingErrorCode(err);

    if (isUserCancelledError(err)) return "plans.payment.cancelled";
    if (code.includes("STORE_BILLING_SDK_KEY_MISSING")) return "plans.payment.notConfigured";
    if (code.includes("STORE_BILLING_WEB_UNSUPPORTED")) return "plans.payment.nativeOnly";
    if (code.includes("STORE_BILLING_PLUGIN_MISSING")) return "plans.payment.pluginMissing";
    if (code.includes("STORE_BILLING_PACKAGE_NOT_FOUND")) return "plans.payment.productUnavailable";
    if (code.includes("STORE_BILLING_TRANSACTION_ID_MISSING")) return "plans.payment.transactionMissing";
    if (code.includes("STORE_VERIFICATION_NOT_CONFIGURED")) return "plans.payment.verifyNotConfigured";
    if (code.includes("NETWORK") || code.includes("Network")) return "plans.payment.networkError";

    return "plans.payment.failed";
  }

  function getRevenueCatApiKey(platform = getPlatform()) {
    return REVENUECAT_PUBLIC_SDK_KEYS[platform] || "";
  }

  async function configure(role) {
    const platform = getPlatform();
    const apiKey = getRevenueCatApiKey(platform);
    const appUserID = getAppUserId(role);
    const Purchases = getNativePurchasesPlugin();

    if (platform !== "ios" && platform !== "android") {
      const err = new Error("STORE_BILLING_WEB_UNSUPPORTED");
      err.code = "STORE_BILLING_WEB_UNSUPPORTED";
      throw err;
    }

    if (!Purchases) {
      const err = new Error("STORE_BILLING_PLUGIN_MISSING");
      err.code = "STORE_BILLING_PLUGIN_MISSING";
      throw err;
    }

    if (!apiKey) {
      const err = new Error("STORE_BILLING_SDK_KEY_MISSING");
      err.code = "STORE_BILLING_SDK_KEY_MISSING";
      throw err;
    }

    if (!appUserID) {
      const err = new Error("STORE_BILLING_USER_MISSING");
      err.code = "STORE_BILLING_USER_MISSING";
      throw err;
    }

    if (configurePromise && configuredAppUserId === appUserID) {
      return configurePromise;
    }

    configuredAppUserId = appUserID;
    configurePromise = Purchases.configure({ apiKey, appUserID }).then(() => ({ appUserID, platform }));
    return configurePromise;
  }

  async function logIn(role) {
    const { appUserID } = await configure(role);
    const Purchases = getNativePurchasesPlugin();

    if (!Purchases?.logIn) {
      const err = new Error("STORE_BILLING_LOGIN_UNAVAILABLE");
      err.code = "STORE_BILLING_LOGIN_UNAVAILABLE";
      throw err;
    }

    return Purchases.logIn({ appUserID });
  }

  async function getOfferings(role) {
    await logIn(role);
    const Purchases = getNativePurchasesPlugin();

    if (!Purchases?.getOfferings) {
      const err = new Error("STORE_BILLING_OFFERINGS_UNAVAILABLE");
      err.code = "STORE_BILLING_OFFERINGS_UNAVAILABLE";
      throw err;
    }

    return Purchases.getOfferings();
  }

  function findPackageByProductId(offerings, productId) {
    const current = offerings?.current;
    const packages = [
      ...(current?.availablePackages || []),
      ...Object.values(offerings?.all || {}).flatMap(offering => offering?.availablePackages || []),
    ];

    return packages.find(pkg => {
      const identifiers = [
        pkg?.product?.identifier,
        pkg?.product?.productIdentifier,
        pkg?.storeProduct?.identifier,
        pkg?.storeProduct?.productIdentifier,
      ].filter(Boolean);

      return identifiers.includes(productId);
    }) || null;
  }

  function getPurchaseTransactionId(result, productId) {
    const transactionId = (
      result?.transaction?.transactionIdentifier ||
      result?.transaction?.transactionId ||
      result?.transaction?.identifier ||
      result?.transactionIdentifier ||
      result?.transactionId ||
      ""
    );

    if (!transactionId) {
      const err = new Error("STORE_BILLING_TRANSACTION_ID_MISSING");
      err.code = "STORE_BILLING_TRANSACTION_ID_MISSING";
      err.product_id = productId;
      throw err;
    }

    return transactionId;
  }

  function getPurchaseExpiresAt(result, productId) {
    const subscriptions = result?.customerInfo?.allExpirationDatesByProduct || {};
    return subscriptions?.[productId] || null;
  }

  async function verifyPurchase({ role, plan, productId, purchaseResult }) {
    if (!window.apiFetch) {
      const err = new Error("STORE_BILLING_API_UNAVAILABLE");
      err.code = "STORE_BILLING_API_UNAVAILABLE";
      throw err;
    }

    const payload = {
      platform: getPlatform(),
      plan: String(plan || "").toLowerCase(),
      product_id: productId,
      transaction_id: getPurchaseTransactionId(purchaseResult, productId),
      original_transaction_id: purchaseResult?.transaction?.originalTransactionIdentifier || null,
      purchase_token: purchaseResult?.transaction?.purchaseToken || null,
      environment: purchaseResult?.transaction?.environment || null,
      expires_at: getPurchaseExpiresAt(purchaseResult, productId),
    };

    return window.apiFetch("/store/verify-purchase", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  async function getCustomerInfo(role) {
    await logIn(role);
    const Purchases = getNativePurchasesPlugin();

    if (!Purchases?.getCustomerInfo) {
      const err = new Error("STORE_BILLING_CUSTOMER_INFO_UNAVAILABLE");
      err.code = "STORE_BILLING_CUSTOMER_INFO_UNAVAILABLE";
      throw err;
    }

    return Purchases.getCustomerInfo();
  }

  async function restorePurchases(role) {
    await logIn(role);
    const Purchases = getNativePurchasesPlugin();

    if (!Purchases?.restorePurchases) {
      const err = new Error("STORE_BILLING_RESTORE_UNAVAILABLE");
      err.code = "STORE_BILLING_RESTORE_UNAVAILABLE";
      throw err;
    }

    return Purchases.restorePurchases();
  }


  async function purchasePlan({ role, plan }) {
    const normalizedRole = String(role || "").toLowerCase();
    const normalizedPlan = String(plan || "").toLowerCase();
    const productId = getProductId(normalizedRole, normalizedPlan);

    if (!productId) {
      throw new Error("INVALID_BILLING_PRODUCT");
    }

    const offerings = await getOfferings(normalizedRole);
    const selectedPackage = findPackageByProductId(offerings, productId);

    if (!selectedPackage) {
      const err = new Error("STORE_BILLING_PACKAGE_NOT_FOUND");
      err.code = "STORE_BILLING_PACKAGE_NOT_FOUND";
      err.product_id = productId;
      throw err;
    }

    const Purchases = getNativePurchasesPlugin();
    if (!Purchases?.purchasePackage) {
      const err = new Error("STORE_BILLING_PURCHASE_UNAVAILABLE");
      err.code = "STORE_BILLING_PURCHASE_UNAVAILABLE";
      err.product_id = productId;
      throw err;
    }

    const purchaseResult = await Purchases.purchasePackage({ aPackage: selectedPackage });
    const verifyResult = await verifyPurchase({
      role: normalizedRole,
      plan: normalizedPlan,
      productId,
      purchaseResult,
    });

    return { purchaseResult, verifyResult };
  }

  function debugState() {
    return {
      platform: getPlatform(),
      appUserId: getAppUserId(),
      hasCapacitor: !!window.Capacitor,
      hasPurchasesPlugin: !!getNativePurchasesPlugin(),
      hasRevenueCatKey: !!getRevenueCatApiKey(),
      configuredAppUserId,
    };
  }

  window.USLYBilling = {
    getProductId,
    getPlatform,
    getAppUserId,
    getNativePurchasesPlugin,
    getBillingErrorCode,
    isUserCancelledError,
    getBillingErrorMessageKey,
    getRevenueCatApiKey,
    configure,
    logIn,
    getOfferings,
    findPackageByProductId,
    verifyPurchase,
    getCustomerInfo,
    restorePurchases,
    debugState,
    purchasePlan,
  };
})();
