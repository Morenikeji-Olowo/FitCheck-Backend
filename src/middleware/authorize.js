export const requirePremium = (req, res, next) => {
  if (req.user?.tier !== 'premium') {
    return res.status(403).json({
      error: 'Premium required',
      message: 'Upgrade to FitCheck Premium to unlock this feature'
    })
  }
  next()
}

export const requireOwnership = (userIdParam = 'userId') => {
  return (req, res, next) => {
    const resourceUserId = req.params[userIdParam]

    if (req.user.id !== resourceUserId) {
      return res.status(403).json({ error: 'Access denied' })
    }
    next()
  }
}