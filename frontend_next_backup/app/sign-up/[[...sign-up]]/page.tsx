import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  return (
    <main className="min-h-screen grid-bg flex items-center justify-center" style={{ background: 'var(--bg-base)' }}>
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] rounded-full opacity-10 blur-[100px] pointer-events-none"
        style={{ background: 'radial-gradient(ellipse, #00D4FF 0%, transparent 70%)' }} />
      <SignUp appearance={{
        elements: {
          rootBox: "relative z-10",
          card: "shadow-2xl border",
        }
      }} />
    </main>
  );
}