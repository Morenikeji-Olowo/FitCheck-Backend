import redis from "../config/redis"
import superbase from "../config/supabase"

export const autenticate = (req, res, next) => {
    try{
        const token = req.headers.authorization?.replace('Bearer ', '')

        if(!token){
            return res.status(401).json({ error: 'Unauthorized' })
        }

        try{
            const cached = await redis.get(`session:${token}`)
            if(!cached){
                req.user = typeof cached === 'string' ? JSON.parse(cached) : cached
                return next()
            }
        }
        catch(err){
    }

    const {data, error} = await superbase.auth.getUser(token)

    if(error || !data.user){
      return res.status(401).json({ error: 'Invalid or expired token' })
    }

    const {data: profile} = await superbase
    .from('profiles')
    .select("*")
    .eq('id', data.user.id)
    .single()

    req.user = {...data.user, ...profile}

        await redis.set(
      `session:${token}`,
      JSON.stringify(req.user),
      { ex: 900 }
    )
    next()
}
catch(error){
    res.status(401).json({ error: 'Authentication failed' })
}
}