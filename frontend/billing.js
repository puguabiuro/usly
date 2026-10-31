(function () {
  const PRODUCT_IDS = {
    ios: {
      user: {
        plus: "usly_user_plus",
        premium: "usly_user_premium",
        vip: "usly_user_vip",
      },
      partner: {
        pro: "usly_partner_pro",
        premium: "usly_partner_premium",
      },
    },
    android: {
      user: {
        plus: "usly_user_plus:monthly",
        premium: "usly_user_premium:monthly",
        vip: "usly_user_vip:monthly",
      },
      partner: {
        pro: "usly_partner_pro:monthly",
        premium: "usly_partner_premium:monthly",
      },
    },
  };

  const REVENUECAT_PUBLIC_SDK_KEYS = Object.freeze({
    ios: window.USLY_CONFIG?.revenueCat?.iosPublicApiKey || "",
    android: window.USLY_CONFIG?.revenueCat?.androidPublicApiKey || "",
  });

  let configurePromise = null;
  let configuredAppUserId = null;
  let identityQueue = Promise.resolve();

  function getProductId(role, plan) {
    const platform = getPlatform();
    const normalizedRole = String(role || "").toLowerCase();
    const normalizedPlan = String(plan || "").toLowerCase();

    return PRODUCT_IDS[platform]?.[normalizedRole]?.[normalizedPlan] || null;
  }

  function getPlatform() {
    const platform = window.Capacitor?.getPlatform?.();
    if (platform === "ios" || platform === "android") return platform;
    return "web";
  }

  function getAppUserId() {
    const appUserId = window.App?.currentRevenueCatAppUserId;
    if (!appUserId) return null;

    return String(appUserId);
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

    if (!configurePromise) {
      configuredAppUserId = appUserID;
      configurePromise = Purchases.configure({ apiKey, appUserID })
        .then(() => ({ appUserID, platform }))
        .catch(error => {
          configurePromise = null;
          configuredAppUserId = null;
          throw error;
        });
    }

    await configurePromise;
    return { appUserID, platform };
  }

  let activeBillingTransactions = 0;

  function isTransactionInProgress() {
    return activeBillingTransactions > 0;
  }

  async function withBillingTransaction(operation) {
    activeBillingTransactions += 1;
    try {
      return await operation();
    } finally {
      activeBillingTransactions -= 1;
    }
  }

  function enqueueBillingOperation(operation) {
    const queued = identityQueue.catch(() => {}).then(operation);
    identityQueue = queued.catch(() => {});
    return queued;
  }

  async function logInNative(role, session) {
    const appUserID = session.revenueCatId;
    assertBillingSession(session);
    await configure(role);
    assertBillingSession(session);

    const Purchases = getNativePurchasesPlugin();

    if (!Purchases?.logIn) {
      const err = new Error("STORE_BILLING_LOGIN_UNAVAILABLE");
      err.code = "STORE_BILLING_LOGIN_UNAVAILABLE";
      throw err;
    }

    const result = await Purchases.logIn({ appUserID });
    assertBillingSession(session);
    return result;
  }

  function logIn(role) {
    const session = captureBillingSession();
    return enqueueBillingOperation(() => logInNative(role, session));
  }

  function getOfferings(role) {
    const session = captureBillingSession();
    return enqueueBillingOperation(async () => {
      await logInNative(role, session);
      const Purchases = getNativePurchasesPlugin();

      if (!Purchases?.getOfferings) {
        const err = new Error("STORE_BILLING_OFFERINGS_UNAVAILABLE");
        err.code = "STORE_BILLING_OFFERINGS_UNAVAILABLE";
        throw err;
      }

      assertBillingSession(session);
      const result = await Purchases.getOfferings();
      assertBillingSession(session);
      return result;
    });
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

  function captureBillingSession() {
    return {
      token: localStorage.getItem("usly_token"),
      userId: String(window.App?.currentUserId ?? ""),
      role: window.App?.role,
      revenueCatId: getAppUserId(),
    };
  }

  function assertBillingSession(session) {
    if (
      !session.token ||
      !session.userId ||
      !session.revenueCatId ||
      localStorage.getItem("usly_token") !== session.token ||
      String(window.App?.currentUserId ?? "") !== session.userId ||
      window.App?.role !== session.role ||
      getAppUserId() !== session.revenueCatId
    ) {
      const error = new Error("STORE_BILLING_SESSION_CHANGED");
      error.code = "STORE_BILLING_SESSION_CHANGED";
      throw error;
    }
  }

  async function syncCurrentRevenueCatPlan(session = captureBillingSession()) {
    assertBillingSession(session);

    if (!window.apiFetch) {
      const err = new Error("STORE_BILLING_API_UNAVAILABLE");
      err.code = "STORE_BILLING_API_UNAVAILABLE";
      throw err;
    }

    return window.apiFetch("/revenuecat/sync-me", {
      method: "POST",
    });
  }

  function getCustomerInfo(role) {
    const session = captureBillingSession();
    return enqueueBillingOperation(async () => {
      await logInNative(role, session);
      const Purchases = getNativePurchasesPlugin();

      if (!Purchases?.getCustomerInfo) {
        const err = new Error("STORE_BILLING_CUSTOMER_INFO_UNAVAILABLE");
        err.code = "STORE_BILLING_CUSTOMER_INFO_UNAVAILABLE";
        throw err;
      }

      assertBillingSession(session);
      const result = await Purchases.getCustomerInfo();
      assertBillingSession(session);
      return result;
    });
  }

  async function restorePurchasesInternal(role) {
    const session = captureBillingSession();
    const restoreResult = await enqueueBillingOperation(async () => {
      await logInNative(role, session);
      const Purchases = getNativePurchasesPlugin();

      if (!Purchases?.restorePurchases) {
        const err = new Error("STORE_BILLING_RESTORE_UNAVAILABLE");
        err.code = "STORE_BILLING_RESTORE_UNAVAILABLE";
        throw err;
      }

      assertBillingSession(session);
      const result = await Purchases.restorePurchases();
      assertBillingSession(session);
      return result;
    });

    const syncResult = await syncCurrentRevenueCatPlan(session);
    return { ...(restoreResult || {}), syncResult };
  }


  function restorePurchases(role) {
    return withBillingTransaction(() => restorePurchasesInternal(role));
  }

  async function purchasePlanInternal({ role, plan }) {
    const session = captureBillingSession();
    assertBillingSession(session);

    const normalizedRole = String(role || "").toLowerCase();
    const normalizedPlan = String(plan || "").toLowerCase();
    const productId = getProductId(normalizedRole, normalizedPlan);

    if (!productId) {
      throw new Error("INVALID_BILLING_PRODUCT");
    }

    if (normalizedRole !== session.role) {
      throw new Error("STORE_BILLING_SESSION_CHANGED");
    }

    const purchaseResult = await enqueueBillingOperation(async () => {
      await logInNative(normalizedRole, session);
      assertBillingSession(session);

      const Purchases = getNativePurchasesPlugin();

      if (!Purchases?.getOfferings) {
        const err = new Error("STORE_BILLING_OFFERINGS_UNAVAILABLE");
        err.code = "STORE_BILLING_OFFERINGS_UNAVAILABLE";
        throw err;
      }

      const offerings = await Purchases.getOfferings();
      assertBillingSession(session);

      const selectedPackage = findPackageByProductId(offerings, productId);

      if (!selectedPackage) {
        const err = new Error("STORE_BILLING_PACKAGE_NOT_FOUND");
        err.code = "STORE_BILLING_PACKAGE_NOT_FOUND";
        err.product_id = productId;
        throw err;
      }

      if (!Purchases?.purchasePackage) {
        const err = new Error("STORE_BILLING_PURCHASE_UNAVAILABLE");
        err.code = "STORE_BILLING_PURCHASE_UNAVAILABLE";
        err.product_id = productId;
        throw err;
      }

      assertBillingSession(session);
      const result = await Purchases.purchasePackage({
        aPackage: selectedPackage,
      });
      assertBillingSession(session);
      return result;
    });

    const syncResult = await syncCurrentRevenueCatPlan(session);
    return { purchaseResult, syncResult };
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

  function purchasePlan(options) {
    return withBillingTransaction(() => purchasePlanInternal(options));
  }

  window.USLYBilling = {
    isTransactionInProgress,
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
    syncCurrentRevenueCatPlan,
    getCustomerInfo,
    restorePurchases,
    debugState,
    purchasePlan,
  };
})();
