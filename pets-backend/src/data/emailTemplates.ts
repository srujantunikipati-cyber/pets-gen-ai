export const templates = [
  {
    name: "petsnapchat_password_reset",
    type: "password_reset",
    subject: "PetSnapChat - Reset Your Password",
    htmlTemplate: `
      <html>
        <body>
          <p>Hi {{USERNAME}},</p>
          <p>Click the button below to reset your password:</p>
          <a href="{{RESET_LINK}}" style="background:#4CAF50;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;">Reset Password</a>
          <p>If the button doesn't work, copy this link: <a href="{{RESET_LINK}}">{{RESET_LINK}}</a></p>
        </body>
      </html>
    `,
    textTemplate: "Hi {{USERNAME}},\nReset your password: {{RESET_LINK}}",
    placeholders: ["RESET_LINK", "USERNAME"],
    createdBy: "system_seed",
  },
  {
    name: "petsnapchat_welcome_email",
    type: "welcome_email",
    subject: "Welcome to PetSnapChat!",
    htmlTemplate: `
      <html>
        <body>
          <h2>Welcome, {{USERNAME}}!</h2>
          <p>Thank you for joining PetSnapChat. Start sharing your pet moments now!</p>
        </body>
      </html>
    `,
    textTemplate: "Welcome, {{USERNAME}}! Thank you for joining PetSnapChat.",
    placeholders: ["USERNAME"],
    createdBy: "system_seed",
  }
];
