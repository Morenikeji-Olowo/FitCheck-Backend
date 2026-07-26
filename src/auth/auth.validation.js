export const validateSignUp = (body) => {
  const { email, fullName, password } = body;
  const errors = {};

  if (!fullName || fullName.trim().length < 2) {
    (errors.fullName ??= []).push('Full name must be at least 2 characters long');
  }
  if (!email || !email.includes('@')) {
    (errors.email ??= []).push('Invalid email address');
  }
  if (!password || password.length < 8) {
    (errors.password ??= []).push('Password must be at least 8 characters long');
  } else {
    if (!/[A-Z]/.test(password)) {
      (errors.password ??= []).push('Password must contain at least one uppercase letter');
    }
    if (!/[0-9]/.test(password)) {
      (errors.password ??= []).push('Password must contain at least one number');
    }
  }

  return errors;
};

export const validateLogin = (body) => {
  const { email, password } = body;
  const errors = {};

  if (!email || !email.includes('@')) {
    (errors.email ??= []).push('Invalid email address');
  }
  if (!password || password.length < 8) {
    (errors.password ??= []).push('Password must be at least 8 characters long');
  }

  return errors;
};

export const validateResetPassword = (body) => {
  const { password } = body;
  const errors = {};

  if (!password || password.length < 8) {
    (errors.password ??= []).push('Password must be at least 8 characters long');
  } else {
    if (!/[A-Z]/.test(password)) {
      (errors.password ??= []).push('Password must contain at least one uppercase letter');
    }
    if (!/[0-9]/.test(password)) {
      (errors.password ??= []).push('Password must contain at least one number');
    }
  }

  return errors;
};

const authValidation = {
  validateSignUp,
  validateLogin,
  validateResetPassword,
};
export default authValidation;