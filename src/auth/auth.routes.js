import express from "express";
import authController from "./auth.controller.js";
import { signUp } from "./auth.controller.js";

const authRouter = express.Router();

authRouter.post("/signup", authController.signUp);
authRouter.post("/login", authController.login);
authRouter.post("/refresh", authController.refresh);
authRouter.post("/forgot-password", authController.forgotPassword);
authRouter.post("/reset-password", authController.resetPassword);

//protected routes
authRouter.get("/me", authController.getMe);
authRouter.post("/logout", authController.logout);
authRouter.delete("/account", authController.deleteAccount);

export default authRouter;