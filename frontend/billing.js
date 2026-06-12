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

  window.USLYBilling = {
    getProductId,
    purchasePlan,
  };
})();
