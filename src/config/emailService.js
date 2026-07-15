import resend from "./email.js";
import { welcomeEmail,
    passwordResetEmail,
    loginAlertEmail,
    accountDeletedEmail
    
 } from "./emailTemplates.js";

const FROM = process.env.EMAIL_FROM || 'noreply@fitcheck.app';

export const sendWelcomeEmail = async(email, fullName) => {
    const template = welcomeEmail(fullName)
    await resend.emails.send({
        from: FROM,
        to: email,
        subject: template.subject,
        html: template.html
    });
}

export const sendPasswordResetEmail  = async (email, resetLink) => {
    const template = passwordResetEmail(resetLink)
    await resend.emails.send({
        from: FROM,
        to: email,
        subject: template.subject,
        html: template.html
    });
}

export const sendLoginAlertEmail= async (email, fullName, time, device) => {
    const template = loginAlertEmail(fullName, time, device)
    await resend.emails.send({
        from: FROM,
        to: email,
        subject: template.subject,
        html: template.html
    });
}
export const sendAccountDeletedEmail = async (email, fullName) => {
  const template = accountDeletedEmail(fullName)
  await resend.emails.send({
    from: FROM,
    to: email,
    subject: template.subject,
    html: template.html
  })
}