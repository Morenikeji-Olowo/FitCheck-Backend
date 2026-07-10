import { createClient } from "@supabase/supabase-js";

const supaBaseUrl = process.env.SUPABASE_URL;
const supaBaseServiceKey = process.env.SUPABASE_SERVICE_KEY;

if(!supaBaseUrl || !supaBaseServiceKey) {
    throw new Error("Supabase URL and Service Key must be provided in environment variables.");
}

const supabase = createClient(supaBaseUrl, supaBaseServiceKey);

export default supabase;