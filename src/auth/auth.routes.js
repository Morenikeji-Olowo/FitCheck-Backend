import express from "express";
import authController from "./auth.controller.js";
import { signUp } from "./auth.controller.js";
import rateLimit from "express-rate-limit";

const authRouter = express.Router();

const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 10, // only 10 attempts per 15 minutes
  message: { error: 'Too many attempts. Please wait a few minutes and try again.' }
})

authRouter.post("/signup",authLimiter, authController.signUp);
authRouter.post("/login", authLimiter, authController.login);
authRouter.post("/refresh", authController.refresh);
authRouter.post("/forgot-password",authLimiter, authController.forgotPassword);
authRouter.post("/reset-password", authController.resetPassword);
authRouter.post("/google", authLimiter,authController.googleLogin);
//protected routes
authRouter.get("/me", authController.getMe);
authRouter.post("/logout", authController.logout);
authRouter.delete("/account", authController.deleteAccount);

export default authRouter;