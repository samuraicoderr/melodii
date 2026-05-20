/**
 * Layo Studio Backend API Routes
 * Keep this file limited to the MVP API surface that the frontend actually uses.
 */

const API_VERSION = "/api/v1";

export const BackendRoutes = {
  auth: {
    login: `${API_VERSION}/auth/login/`,
    refresh: `${API_VERSION}/auth/login/refresh_token/`,
    register: `${API_VERSION}/auth/register/`,
    checkUsername: `${API_VERSION}/auth/check_username/`,
    joinWaitlist: `${API_VERSION}/auth/join_waitlist/`,

    me: `${API_VERSION}/users/me/`,
    updateMe: `${API_VERSION}/users/update_me/`,
    deleteMe: `${API_VERSION}/users/delete_me/`,
    memberships: `${API_VERSION}/users/memberships/`,
    activeOrganization: `${API_VERSION}/users/active-org/`,

    changePassword: `${API_VERSION}/security/password/`,
    sendForgotPasswordOtp: `${API_VERSION}/security/password/send_forgot_password_otp/`,
    resetForgotPassword: `${API_VERSION}/security/password/reset_forgot_password/`,

    mfa: {
      qrImage: (token: string) => `${API_VERSION}/auth/mfa/authapp/qr-image/${token}/`,
      requestQrCode: `${API_VERSION}/auth/mfa/authapp/request_qr_code/`,
      challenge: `${API_VERSION}/auth/mfa/challenge/`,
      methods: `${API_VERSION}/auth/mfa/methods/`,
      pushRegisterDevice: `${API_VERSION}/auth/mfa/push/register-device/`,
      setupTotp: `${API_VERSION}/auth/mfa/setup/totp/`,
      setupWebauthn: `${API_VERSION}/auth/mfa/setup/webauthn/`,
      verify: `${API_VERSION}/auth/mfa/verify/`,
      verifyTotp: `${API_VERSION}/auth/mfa/verify/totp/`,
      verifyWebauthn: `${API_VERSION}/auth/mfa/verify/webauthn/`,
    },

    onboarding: {
      sendEmailOtp: `${API_VERSION}/auth/onboarding/email/send_email_verification_otp/`,
      checkEmailOtp: `${API_VERSION}/auth/onboarding/email/check_email_verification_otp/`,
      sendPhoneOtp: `${API_VERSION}/auth/onboarding/phone/send_phone_verification_otp/`,
      checkPhoneOtp: `${API_VERSION}/auth/onboarding/phone/check_phone_verification_otp/`,
      getOnboardingToken: `${API_VERSION}/auth/onboarding/get_onboarding_token/`,
      getUserData: `${API_VERSION}/auth/onboarding/get_user_data/`,
      setUserBasicInfo: `${API_VERSION}/auth/onboarding/set_user_basic_info/`,
      setPassword: `${API_VERSION}/auth/onboarding/set_password/`,
      setUsername: `${API_VERSION}/auth/onboarding/set_username/`,
      setProfilePicture: `${API_VERSION}/auth/onboarding/set_profile_picture/`,
      exchangeTokens: `${API_VERSION}/auth/onboarding/exchange_onboarding_tokens_for_login_tokens/`,
        createOrganization: `${API_VERSION}/auth/onboarding/organization/create_organization/`,
        fetchOrganizationInvites: `${API_VERSION}/auth/onboarding/organization/fetch_organization_invites/`,
        acceptOrRejectOrganizationInvite: `${API_VERSION}/auth/onboarding/organization/accept_or_reject_organization_invite/`,
    },

    requestQrCode: `${API_VERSION}/auth/mfa/authapp/request_qr_code/`,
    check2faOtp: `${API_VERSION}/auth/mfa/verify/`,
    sendEmailOtp: `${API_VERSION}/auth/onboarding/email/send_email_verification_otp/`,
    sendPhoneOtp: `${API_VERSION}/auth/onboarding/phone/send_phone_verification_otp/`,
    checkEmailOtp: `${API_VERSION}/auth/onboarding/email/check_email_verification_otp/`,
    checkPhoneOtp: `${API_VERSION}/auth/onboarding/phone/check_phone_verification_otp/`,
    getOnboardingToken: `${API_VERSION}/auth/onboarding/get_onboarding_token/`,
    setBasicInfo: `${API_VERSION}/auth/onboarding/set_user_basic_info/`,
    setPassword: `${API_VERSION}/auth/onboarding/set_password/`,
    setUsername: `${API_VERSION}/auth/onboarding/set_username/`,
    setProfilePicture: `${API_VERSION}/auth/onboarding/set_profile_picture/`,
    exchangeOnboardingTokens: `${API_VERSION}/auth/onboarding/exchange_onboarding_tokens_for_login_tokens/`,
  },

  organizations: {
    base: `${API_VERSION}/organizations/`,
    detail: (id: string) => `${API_VERSION}/organizations/${id}/`,
    memberships: (organizationId: string) => `${API_VERSION}/organizations/${organizationId}/memberships/`,
    roles: (organizationId: string) => `${API_VERSION}/organizations/${organizationId}/roles/`,
    invitations: (organizationId: string) => `${API_VERSION}/organizations/${organizationId}/invitations/`,
    invitation: (organizationId: string, invitationId: string) =>
      `${API_VERSION}/organizations/${organizationId}/invitations/${invitationId}/`,
  },

  dashboard: {
    summary: `${API_VERSION}/dashboard/summary/`,
  },

  operations: {
    summary: (organizationId: string) => `${API_VERSION}/organizations/${organizationId}/operations-summary/`,
    projects: (organizationId: string) => `${API_VERSION}/organizations/${organizationId}/projects/`,
    project: (organizationId: string, id: string) => `${API_VERSION}/organizations/${organizationId}/projects/${id}/`,
    projectMembers: (organizationId: string) => `${API_VERSION}/organizations/${organizationId}/project-members/`,
    chapters: (organizationId: string) => `${API_VERSION}/organizations/${organizationId}/chapters/`,
    chapter: (organizationId: string, id: string) => `${API_VERSION}/organizations/${organizationId}/chapters/${id}/`,
    artifacts: (organizationId: string) => `${API_VERSION}/organizations/${organizationId}/artifacts/`,
    artifact: (organizationId: string, id: string) => `${API_VERSION}/organizations/${organizationId}/artifacts/${id}/`,
    artifactRevisions: (organizationId: string, artifactId: string) =>
      `${API_VERSION}/organizations/${organizationId}/artifacts/${artifactId}/revisions/`,
    artifactRevision: (organizationId: string, artifactId: string, revisionId: string) =>
      `${API_VERSION}/organizations/${organizationId}/artifacts/${artifactId}/revisions/${revisionId}/`,
    approveArtifactRevision: (organizationId: string, artifactId: string, revisionId: string) =>
      `${API_VERSION}/organizations/${organizationId}/artifacts/${artifactId}/revisions/${revisionId}/approve/`,
    paymentEntries: (organizationId: string) => `${API_VERSION}/organizations/${organizationId}/payment-entries/`,
    authorizePaymentEntries: (organizationId: string) =>
      `${API_VERSION}/organizations/${organizationId}/payment-entries/authorize/`,
    payoutBatches: (organizationId: string) => `${API_VERSION}/organizations/${organizationId}/payout-batches/`,
    payoutBatch: (organizationId: string, id: string) => `${API_VERSION}/organizations/${organizationId}/payout-batches/${id}/`,
    markPayoutBatchPaid: (organizationId: string, id: string) =>
      `${API_VERSION}/organizations/${organizationId}/payout-batches/${id}/mark-paid/`,
    payoutSchedules: (organizationId: string) => `${API_VERSION}/organizations/${organizationId}/payout-schedules/`,
    logs: `${API_VERSION}/logs/`,
    payments: `${API_VERSION}/payments/`,
    payment: (id: string) => `${API_VERSION}/payments/${id}/`,
    team: `${API_VERSION}/team/`,
    inviteTeamMember: `${API_VERSION}/team/invitations/`,
    reports: {
      productivity: `${API_VERSION}/reports/productivity/`,
      financial: `${API_VERSION}/reports/financial/`,
    },
  },

  wellness: {
    assessments: `${API_VERSION}/assessments/`,
    submitAssessment: `${API_VERSION}/assessments/submit/`,
    latestAssessment: `${API_VERSION}/assessments/latest/`,
    assessmentHistory: `${API_VERSION}/assessments/history/`,
    questionnaires: `${API_VERSION}/assessments/questionnaires/`,
    assessmentDetail: (id: string) => `${API_VERSION}/assessments/${id}/`,
    recommendations: `${API_VERSION}/recommendations/`,
    dismissRecommendation: (id: string) => `${API_VERSION}/recommendations/${id}/dismiss/`,
    moodLogs: `${API_VERSION}/mood-logs/`,
    moodSummary: `${API_VERSION}/mood-logs/summary/`,
    todayMoodLog: `${API_VERSION}/mood-logs/today/`,
    insightsSummary: `${API_VERSION}/insights/summary/`,
    chatConversations: `${API_VERSION}/chat/conversations/`,
    activeChatConversation: `${API_VERSION}/chat/conversations/active/`,
    chatConversationDetail: (id: string) => `${API_VERSION}/chat/conversations/${id}/`,
    renameChatConversation: (id: string) => `${API_VERSION}/chat/conversations/${id}/rename/`,
    chatMessages: (id: string) => `${API_VERSION}/chat/conversations/${id}/messages/`,
    sendChatMessage: (id: string) => `${API_VERSION}/chat/conversations/${id}/send-message/`,
    editChatMessage: (id: string) => `${API_VERSION}/chat/conversations/${id}/edit-message/`,
    regenerateChatMessage: (id: string) => `${API_VERSION}/chat/conversations/${id}/regenerate-message/`,
  },

  passwordReset: {
    request: `${API_VERSION}/reset/`,
    confirm: `${API_VERSION}/reset/confirm/`,
    renderResetPage: `${API_VERSION}/reset/confirm/render_reset_page/`,
    validateToken: `${API_VERSION}/reset/validate_token/`,
  },

  realtime: {
    websocket: (token: string) => `ws://localhost:9000/ws/melodii/?token=${token}`,
  },

  genreAi: {
    classify: `${API_VERSION}/genre-ai/classify/`,
  },

  me: `${API_VERSION}/users/me/`,
  userMemberships: `${API_VERSION}/users/memberships/`,
  setActiveOrganization: `${API_VERSION}/users/active-org/`,
  loginFirstFactor: `${API_VERSION}/auth/login/`,
  refreshToken: `${API_VERSION}/auth/login/refresh_token/`,
  register: `${API_VERSION}/auth/register/`,
  checkUsername: `${API_VERSION}/auth/check_username/`,
  joinWaitlist: `${API_VERSION}/auth/join_waitlist/`,
  updateMe: `${API_VERSION}/users/update_me/`,
  deleteMe: `${API_VERSION}/users/delete_me/`,
  changePassword: `${API_VERSION}/security/password/`,
  sendForgotPasswordOtp: `${API_VERSION}/security/password/send_forgot_password_otp/`,
  resetForgotPassword: `${API_VERSION}/security/password/reset_forgot_password/`,

  getUsers: `${API_VERSION}/users/`,
  getUser: (id: string) => `${API_VERSION}/users/${id}/`,
  updatePassword: `${API_VERSION}/security/password/`,
  resetRecoveryCodes: `${API_VERSION}/security/2fa/reset_recovery_codes/`,

  requestQrCode: `${API_VERSION}/auth/mfa/authapp/request_qr_code/`,
  check2faOtp: `${API_VERSION}/auth/mfa/verify/`,

  sendEmailOtp: `${API_VERSION}/auth/onboarding/email/send_email_verification_otp/`,
  sendPhoneOtp: `${API_VERSION}/auth/onboarding/phone/send_phone_verification_otp/`,
  checkEmailOtp: `${API_VERSION}/auth/onboarding/email/check_email_verification_otp/`,
  checkPhoneOtp: `${API_VERSION}/auth/onboarding/phone/check_phone_verification_otp/`,
  getOnboardingToken: `${API_VERSION}/auth/onboarding/get_onboarding_token/`,
  onboardingSendEmailOtp: `${API_VERSION}/auth/onboarding/email/send_email_verification_otp/`,
  onboardingCheckEmailOtp: `${API_VERSION}/auth/onboarding/email/check_email_verification_otp/`,
  onboardingSendPhoneOtp: `${API_VERSION}/auth/onboarding/phone/send_phone_verification_otp/`,
  onboardingCheckPhoneOtp: `${API_VERSION}/auth/onboarding/phone/check_phone_verification_otp/`,
  onboardingSetUserBasicInfo: `${API_VERSION}/auth/onboarding/set_user_basic_info/`,
  onboardingSetPassword: `${API_VERSION}/auth/onboarding/set_password/`,
  onboardingSetUsername: `${API_VERSION}/auth/onboarding/set_username/`,
  onboardingSetProfilePicture: `${API_VERSION}/auth/onboarding/set_profile_picture/`,
  onboardingGetUserData: `${API_VERSION}/auth/onboarding/get_user_data/`,
  onboardingExchangeTokens: `${API_VERSION}/auth/onboarding/exchange_onboarding_tokens_for_login_tokens/`,
  onboardingCreateOrganization: `${API_VERSION}/auth/onboarding/organization/create_organization/`,
  onboardingFetchOrganizationInvites: `${API_VERSION}/auth/onboarding/organization/fetch_organization_invites/`,
  onboardingAcceptOrRejectOrganizationInvite: `${API_VERSION}/auth/onboarding/organization/accept_or_reject_organization_invite/`,

  oauthAuthorizeCode: (provider: string) => `${API_VERSION}/oauth/${provider}/login-or-register/`,
  oauthLoginOrRegister: (provider: string) => `${API_VERSION}/oauth/${provider}/login-or-register/`,
  oauthGetProviders: `${API_VERSION}/oauth/get_providers/`,

  notifications: `${API_VERSION}/notifications/`,
  notificationsUnreadCount: `${API_VERSION}/notifications/unread-count/`,
  notificationMarkRead: (id: string) => `${API_VERSION}/notifications/${id}/read/`,
  notificationsMarkAllRead: `${API_VERSION}/notifications/mark-all-read/`,
  logs: `${API_VERSION}/logs/`,
  payments: `${API_VERSION}/payments/`,
  payment: (id: string) => `${API_VERSION}/payments/${id}/`,
  team: `${API_VERSION}/team/`,
  reports: {
    productivity: `${API_VERSION}/reports/productivity/`,
    financial: `${API_VERSION}/reports/financial/`,
  },
} as const;

export default BackendRoutes;
