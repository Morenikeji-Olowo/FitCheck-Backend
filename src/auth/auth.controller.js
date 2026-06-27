import authService, { getProfile, logoutUser, signUpUser } from "./auth.service.js"
import authValidation, { validateSignUp } from "./auth.validation.js"

export const signUp = async (req, res) => {
    try{
        const errors = validateSignUp(req.body)
        if(errors.length > 0){
            return res.status(400).json({ errors })
        }

        const {email, fullName, password} = req.body
        const user = await authService.signUpUser({email, fullName, password})

        res.status(201).json({ 
            message: 'Account created successfully, please check your email to verify your account',
            userId: user.id
        })
    }
    catch(error){
        res.status(400).json({ error: error.message })
    }
}

export const login = async (req, res) => {
    try{
        const errors = authValidation.validateLogin(req.body)
        if(errors.length > 0){
            return res.status(400).json({ errors })
        }

        const {email, password} = req.body
        const result = await authService.loginUser({email, password})

        res.json({
            message: 'Login successful',
            user: {
                id: result.user.id,
                email: result.user.email
            },
            access_token: result.accesss_token,
            refresh_token: result.refresh_token
        })
    }
    catch(error){
        res.status(400).json({ error: error.message })
    }
}

export const refresh = async (req,res) =>{
    try{
        const {refresh_token } = req.body;

        if(!refresh_token){
            return res.status(400).json({ error: 'Refresh token is required' })
        }

        const tokens = await refreshToken(refresh_token)
        res.json({
            message: 'Token refreshed successfully',
            tokens: tokens
        })
    }
    catch(error){
        res.status(400).json({ error: error.message })
    }
}

export const forgotPassword = async (req, res) => {
    try{
        const {email} = req.body

        if(!email || !email.includes('@')){
            return res.status(400).json({ error: 'Invalid email address' })
        }

        await forgotPassword(email)
        res.json({ message: 'Password reset email sent, please check your inbox' })
    }
    catch(error){
        res.status(400).json({ error: error.message })
    }
}

export const resetPassword = async (req, res) => {
    try{
        const errors = validateResetPassword(req.body)
        if(errors.length > 0){
            return res.status(400).json({ errors })
        }

        const {password} = req.body
        await resetPassword(password)

        res.json({ message: 'Password reset successful, you can now login with your new password' })
    }
    catch(error){
        res.status(400).json({ error: error.message })
    }
}

export const logout = async (req, res) => {
    try{
        const token = req.headers.authorization?.split('Bearer ', '')[1]
        await logoutUser(token)
        res.json({ message: 'Logout successful' })
    }
    catch(error){
        res.status(400).json({ error: error.message })
    }
}

export const getMe = async (req, res) => {
    try{
        const profile = await getProfile(req.user.id)
        res.json({ user: profile })
    }
    catch(error){
        res.status(400).json({ error: error.message })
    }
}

export const deleteAccount = async (req, res) => {
  try {
    const token = req.headers.authorization?.replace('Bearer ', '')
    await deleteAccount(req.user.id, token)
    res.json({ message: 'Account deleted successfully' })
  } catch (error) {
    res.status(400).json({ error: error.message })
  }
}

const authController = {
    signUp,
    login,
    refresh,
    forgotPassword,
    resetPassword,
    logout,
    getMe,
    deleteAccount
}
export default authController;