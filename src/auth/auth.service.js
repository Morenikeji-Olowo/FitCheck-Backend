import redis from "../config/redis.js";
import superbase from "../config/supabase.js"

export const signUpUser = async ({email, password, fullName}) =>{
    const {data, error} = await superbase.auth.signUp({
        email,
        password,
        options: {
            data: {
                full_name: fullName
            }
        }
    })

    if (error) {
    if (error.message.includes('already registered')) {
        throw new Error('An account with this email already exists')
    }
    throw new Error(error.message)
    }

    const {error: profileError} = await superbase

    .from('profiles')
    .insert({
        id: data.user.id,
        full_name: fullName,
        email,
        tier: "free"
    })

    if(profileError) throw new Error(profileError.message);

    return data.user
}

export const loginUser = async ({email, password}) => {
    const {data, error} = await superbase.auth.signInWithPassword({
        email,
        password
    })
    if(error) throw new Error (error.message);
    
    return{
        user: data.user,
        accesss_token: data.session.access_token,
        refresh_token:data.session.refresh_token
    }
}

export const refreshToken = async (refresh_token) => {
    const {data, error} = superbase.auth.refreshSession({
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
    const {error} = await superbase.auth.updateUser({
        password
    })
    if(error) throw new Error(error.message);
}

export const logoutUser = async (token) => {
    await superbase.auth.signOut()
    await redis.del(`session:${token}`)
}

export const getProfile = async (userId) => {
    const {data, error} = await superbase
    .from('profiles')
    .select('*')
    .eq('id', userId)
    .single()

    if(error) throw new Error(error.message);

    return data
}

export const deleteProfile = async (userId, token) => {
    const {error} = await superbase
    .from('profiles')
    .delete()
    .eq('id', userId)

    if(error) throw new Error(error.message);

    await superbase.auth.admin.deleteUser(userId);
    
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