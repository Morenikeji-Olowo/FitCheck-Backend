import redis from "../config/redis.js";
import supabase from "../config/supabase.js";

export const authenticate = async (req, res, next) => {
  try {
    const token = req.headers.authorization?.replace('Bearer ', '');

    if (!token) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    try {
      const cached = await redis.get(`session:${token}`);
      if (cached) {
        req.user = typeof cached === 'string' ? JSON.parse(cached) : cached;
        return next();
      }
    } catch (err) {
      // Redis read failed — fall through to Supabase verification below
      // instead of failing the request outright.
    }

    const { data, error } = await supabase.auth.getUser(token);

    if (error || !data.user) {
      return res.status(401).json({ error: 'Invalid or expired token' });
    }

    const { data: profile } = await supabase
      .from('profiles')
      .select('*')
      .eq('id', data.user.id)
      .single();

    req.user = { ...data.user, ...profile };

    await redis.set(`session:${token}`, JSON.stringify(req.user), { ex: 900 });

    next();
  } catch (error) {
    res.status(401).json({ error: 'Authentication failed' });
  }
};

export const requirePremium = (req, res, next) => {
  if (req.user?.tier !== 'premium') {
    return res.status(403).json({
      error: 'Premium required',
      message: 'Upgrade to FitCheck Premium to unlock this feature',
    });
  }
  next();
};

export const requireOwnership = (userIdParam = 'userId') => {
  return (req, res, next) => {
    const resourceUserId = req.params[userIdParam];

    if (req.user.id !== resourceUserId) {
      return res.status(403).json({ error: 'Access denied' });
    }
    next();
  };
};