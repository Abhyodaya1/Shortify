// Supabase Integration & Mock Layer
// Allows zero-friction local development without requiring external cloud accounts or npm network installs.

export const isSupabaseConfigured = Boolean(
  typeof process !== "undefined" &&
  process.env.NEXT_PUBLIC_SUPABASE_URL &&
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
);

export const supabase = {
  auth: {
    getUser: async () => ({
      data: {
        user: {
          id: "usr_abhyodaya_default",
          email: "abhyodayasingh00@gmail.com",
          user_metadata: { full_name: "Abhyodaya Singh" },
        },
      },
      error: null,
    }),
    signOut: async () => ({ error: null }),
  },
};
