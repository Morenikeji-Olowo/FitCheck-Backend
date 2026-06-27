import { createClient } from "@supabase/supabase-js";

const superBaseUrl = process.env.SUPABASE_URL;
const superBaseServiceKey = process.env.SUPABASE_SERVICE_KEY;

if(!superBaseUrl || !superBaseServiceKey) {
    throw new Error("Supabase URL and Service Key must be provided in environment variables.");
}

const superbase = createClient(superBaseUrl, superBaseServiceKey);

export default superbase;