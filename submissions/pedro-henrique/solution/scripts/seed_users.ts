import { createClient } from "@supabase/supabase-js";

async function main() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!url || !serviceKey) {
    throw new Error("Defina NEXT_PUBLIC_SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY");
  }

  const supabase = createClient(url, serviceKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  });

  const users = [
    { email: "admin@g4.local", password: "Admin123!", role: "admin", full_name: "Pedro Admin" },
    { email: "customer1@g4.local", password: "Customer123!", role: "customer", full_name: "Cliente 1" },
    { email: "customer2@g4.local", password: "Customer123!", role: "customer", full_name: "Cliente 2" },
  ];

  for (const user of users) {
    const { data, error } = await supabase.auth.admin.createUser({
      email: user.email,
      password: user.password,
      email_confirm: true,
    });

    if (error) {
      console.error("Erro ao criar usuário", user.email, error.message);
      continue;
    }

    if (!data.user?.id) {
      continue;
    }

    await supabase.from("profiles").upsert({
      id: data.user.id,
      email: user.email,
      full_name: user.full_name,
      role: user.role,
    });

    console.log("Usuário pronto:", user.email);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
