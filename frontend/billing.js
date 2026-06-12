(function () {
  const PRODUCT_IDS = {
    user: {
      plus: "usly_user_plus_monthly",
      premium: "usly_user_premium_monthly",
      vip: "usly_user_vip_monthly",
    },
    partner: {
      pro: "usly_partner_pro_monthly",
      premium: "usly_partner_premium_monthly",
    },
  };

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

  async function purchasePlan({ role, plan }) {
    const normalizedRole = String(role || "").toLowerCase();
    const normalizedPlan = String(plan || "").toLowerCase();
    const productId = getProductId(normalizedRole, normalizedPlan);

    if (!productId) {
      throw new Error("INVALID_BILLING_PRODUCT");
    }

    const err = new Error("STORE_BILLING_NOT_READY");
    err.code = "STORE_BILLING_NOT_READY";
    err.product_id = productId;
    throw err;
  }

  function debugState() {
    return {
      platform: getPlatform(),
      appUserId: getAppUserId(),
      hasCapacitor: !!window.Capacitor,
      hasPurchasesPlugin: !!getNativePurchasesPlugin(),
    };
  }

  window.USLYBilling = {
    getProductId,
    getPlatform,
    getAppUserId,
    getNativePurchasesPlugin,
    debugState,
    purchasePlan,
  };
})();
