import redis from "../config/redis.js";
import supabase from "../config/supabase.js";
export const signUpUser = async ({ email, password, fullName }) => {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: { full_name: fullName }
    }
  })

  if (error) {
    // Intercept Supabase auth errors
    if (error.message.includes('already registered')) {
      throw new Error('An account with this email already exists. Please log in instead.')
    }
    if (error.message.includes('invalid email')) {
      throw new Error('Please enter a valid email address.')
    }
    if (error.message.includes('weak password')) {
      throw new Error('Your password is too weak. Use at least 8 characters with a number and uppercase letter.')
    }
    throw new Error('Something went wrong creating your account. Please try again.')
  }

  const { error: profileError } = await supabase
    .from('profiles')
    .insert({
      id: data.user.id,
      full_name: fullName,
      email,
      tier: 'free'
    })

  if (profileError) {
    // Intercept database errors
    if (profileError.message.includes('duplicate key') || 
        profileError.message.includes('unique constraint')) {
      throw new Error('An account with this email already exists. Please log in instead.')
    }
    if (profileError.message.includes('null value')) {
      throw new Error('Please fill in all required fields.')
    }
    throw new Error('Something went wrong setting up your profile. Please try again.')
  }

  return data.user
}

export const loginUser = async ({ email, password }) => {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password
  })

  if (error) {
    if (error.message.includes('Invalid login credentials')) {
      throw new Error('Incorrect email or password. Please try again.')
    }
    if (error.message.includes('Email not confirmed')) {
      throw new Error('Please confirm your email before logging in. Check your inbox.')
    }
    if (error.message.includes('too many requests')) {
      throw new Error('Too many login attempts. Please wait a few minutes and try again.')
    }
    throw new Error('Something went wrong logging in. Please try again.')
  }

  return {
    user: data.user,
    access_token: data.session.access_token,
    refresh_token: data.session.refresh_token
  }
}

export const refreshToken = async (refresh_token) => {
    const {data, error} = supabase.auth.refreshSession({
        refresh_token
    })
  if (error) throw new Error('Session expired, please login again');

  return{
    access_token: data.session.access_token,
    refresh_token: data.session.refresh_token
  }
}

export const forgotPassword = async (email) =>{
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: 'fitcheck://reset-password'
    });
    if (error) throw new Error(error.message);
}

export const resetPassword = async (password) => {
    const {error} = await supabase.auth.updateUser({
        password
    })
    if(error) throw new Error(error.message);
}

export const logoutUser = async (token) => {
    await supabase.auth.signOut()
    await redis.del(`session:${token}`)
}

export const getProfile = async (userId) => {
    const {data, error} = await supabase
    .from('profiles')
    .select('*')
    .eq('id', userId)
    .single()

    if(error) throw new Error(error.message);

    return data
}

export const deleteProfile = async (userId, token) => {
    const {error} = await supabase
    .from('profiles')
    .delete()
    .eq('id', userId)

    if(error) throw new Error(error.message);

    await supabase.auth.admin.deleteUser(userId);
    
    await redis.del(`session:${token}`)
}

const authService = {
    signUpUser,
    loginUser,
    refreshToken,
    forgotPassword,
    resetPassword,
    logoutUser,
    getProfile,
    deleteProfile
}
export default authService; 