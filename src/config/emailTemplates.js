export const welcomeEmail = (fullName) => ({
  subject: 'Welcome to FitCheck ✦',
  html: `
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0A0A0A; color: #F5F0EB; padding: 40px; border-radius: 12px;">
      
      <h1 style="font-size: 28px; font-weight: 700; margin-bottom: 8px;">
        Welcome to FitCheck ✦
      </h1>
      
      <p style="color: #9CA3AF; font-size: 16px; margin-bottom: 32px;">
        Your wardrobe. Reimagined.
      </p>

      <p style="font-size: 16px; line-height: 1.6;">
        Hey ${fullName}, you're in. 👋
      </p>

      <p style="font-size: 16px; line-height: 1.6; color: #D1D5DB;">
        FitCheck is your personal AI stylist — built around your body, 
        your wardrobe, and your life. Start by adding your first item 
        to your closet.
      </p>

      <a href="https://fitcheck.app/closet" 
         style="display: inline-block; background: #6366F1; color: white; 
                padding: 14px 28px; border-radius: 8px; text-decoration: none; 
                font-weight: 600; font-size: 16px; margin-top: 24px;">
        Build Your Closet →
      </a>

      <hr style="border: none; border-top: 1px solid #1F2937; margin: 40px 0;" />

      <p style="font-size: 13px; color: #6B7280;">
        You're receiving this because you signed up for FitCheck.<br/>
        © 2025 FitCheck. All rights reserved.
      </p>

    </div>
  `
})

export const passwordResetEmail = (resetLink) => ({
  subject: 'Reset your FitCheck password',
  html: `
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0A0A0A; color: #F5F0EB; padding: 40px; border-radius: 12px;">
      
      <h1 style="font-size: 28px; font-weight: 700; margin-bottom: 8px;">
        Password Reset
      </h1>

      <p style="font-size: 16px; line-height: 1.6; color: #D1D5DB;">
        We received a request to reset your FitCheck password. 
        Click the button below to set a new one.
      </p>

      <a href="${resetLink}" 
         style="display: inline-block; background: #6366F1; color: white; 
                padding: 14px 28px; border-radius: 8px; text-decoration: none; 
                font-weight: 600; font-size: 16px; margin-top: 24px;">
        Reset Password →
      </a>

      <p style="font-size: 14px; color: #6B7280; margin-top: 24px;">
        This link expires in 1 hour. If you didn't request this, 
        ignore this email — your account is safe.
      </p>

      <hr style="border: none; border-top: 1px solid #1F2937; margin: 40px 0;" />

      <p style="font-size: 13px; color: #6B7280;">
        © 2025 FitCheck. All rights reserved.
      </p>

    </div>
  `
})

export const loginAlertEmail = (fullName, time, device) => ({
  subject: 'New login to your FitCheck account',
  html: `
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0A0A0A; color: #F5F0EB; padding: 40px; border-radius: 12px;">
      
      <h1 style="font-size: 28px; font-weight: 700; margin-bottom: 8px;">
        New Login Detected
      </h1>

      <p style="font-size: 16px; line-height: 1.6; color: #D1D5DB;">
        Hey ${fullName}, we noticed a new login to your FitCheck account.
      </p>

      <div style="background: #111827; border-radius: 8px; padding: 20px; margin: 24px 0;">
        <p style="margin: 0; font-size: 14px; color: #9CA3AF;">Time</p>
        <p style="margin: 4px 0 16px; font-size: 16px;">${time}</p>
        <p style="margin: 0; font-size: 14px; color: #9CA3AF;">Device</p>
        <p style="margin: 4px 0 0; font-size: 16px;">${device}</p>
      </div>

      <p style="font-size: 15px; color: #D1D5DB;">
        If this was you, no action needed. If this wasn't you, 
        reset your password immediately.
      </p>

      <a href="https://fitcheck.app/reset-password" 
         style="display: inline-block; background: #EF4444; color: white; 
                padding: 14px 28px; border-radius: 8px; text-decoration: none; 
                font-weight: 600; font-size: 16px; margin-top: 16px;">
        Secure My Account →
      </a>

      <hr style="border: none; border-top: 1px solid #1F2937; margin: 40px 0;" />

      <p style="font-size: 13px; color: #6B7280;">
        © 2025 FitCheck. All rights reserved.
      </p>

    </div>
  `
})

export const accountDeletedEmail = (fullName) => ({
  subject: 'Your FitCheck account has been deleted',
  html: `
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0A0A0A; color: #F5F0EB; padding: 40px; border-radius: 12px;">
      
      <h1 style="font-size: 28px; font-weight: 700; margin-bottom: 8px;">
        Account Deleted
      </h1>

      <p style="font-size: 16px; line-height: 1.6; color: #D1D5DB;">
        Hey ${fullName}, your FitCheck account and all associated data 
        has been permanently deleted as requested.
      </p>

      <p style="font-size: 15px; color: #D1D5DB;">
        We're sorry to see you go. If you ever want to come back, 
        you can always create a new account.
      </p>

      <p style="font-size: 14px; color: #6B7280; margin-top: 24px;">
        If you didn't request this deletion, please contact us immediately 
        at support@fitcheck.app
      </p>

      <hr style="border: none; border-top: 1px solid #1F2937; margin: 40px 0;" />

      <p style="font-size: 13px; color: #6B7280;">
        © 2025 FitCheck. All rights reserved.
      </p>

    </div>
  `
})