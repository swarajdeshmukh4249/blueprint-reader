import { Check, Copy, Mail } from 'lucide-react'
import { useMemo, useState } from 'react'
import Container from '@/components/Container'
import { cn } from '@/lib/utils'

function getContactEmail() {
  const raw = import.meta.env.VITE_CONTACT_EMAIL as string | undefined
  return raw ?? 'hello@blueprintreader.ai'
}

export default function Contact() {
  const email = useMemo(() => getContactEmail(), [])
  const [name, setName] = useState('')
  const [fromEmail, setFromEmail] = useState('')
  const [message, setMessage] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const valid =
    name.trim().length >= 2 &&
    fromEmail.includes('@') &&
    fromEmail.includes('.') &&
    message.trim().length >= 10

  return (
    <div className="pb-16">
      <Container className="pt-10 md:pt-14">
        <div className="grid gap-10 md:grid-cols-12">
          <div className="space-y-5 md:col-span-5">
            <div className="text-xs tracking-[0.22em] text-ink/55">CONTACT</div>
            <h1 className="font-display text-4xl leading-[0.95] tracking-tight md:text-5xl">
              Let’s talk
              <span className="block text-ink/80">about your drawings.</span>
            </h1>
            <p className="max-w-md text-sm leading-relaxed text-ink/70">
              Share a sample blueprint, your target outputs, or a preferred workflow. This UI is
              built to feel innovative—but still studio-professional.
            </p>

            <div className="rounded-2xl border border-ink/10 bg-paper/60 p-5 shadow-[0_12px_36px_hsl(var(--shadow)/0.08)]">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="text-xs tracking-[0.2em] text-ink/55">EMAIL</div>
                  <div className="mt-1 truncate text-sm font-medium">{email}</div>
                </div>
                <button
                  type="button"
                  onClick={() => navigator.clipboard.writeText(email)}
                  className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-ink/12 bg-paper/60 text-ink/75 transition hover:bg-paper hover:text-ink"
                  aria-label="Copy email address"
                >
                  <Copy className="h-4 w-4" />
                </button>
              </div>
              <a
                href={`mailto:${email}`}
                className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-full bg-ink px-5 py-3 text-sm font-medium text-paper transition hover:-translate-y-px hover:bg-ink/90"
              >
                <Mail className="h-4 w-4" />
                Open email
              </a>
            </div>
          </div>

          <div className="md:col-span-7">
            <div className="rounded-3xl border border-ink/10 bg-paper/60 p-7 shadow-soft">
              {submitted ? (
                <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-ink/10 bg-paper-2/60 text-ink">
                    <Check className="h-6 w-6" />
                  </div>
                  <div className="font-display text-3xl tracking-tight">Message prepared</div>
                  <div className="max-w-sm text-sm text-ink/70">
                    Your email client should open with the details. If it doesn’t, copy the email and
                    send it manually.
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setSubmitted(false)
                      setName('')
                      setFromEmail('')
                      setMessage('')
                    }}
                    className="mt-2 inline-flex rounded-full border border-ink/12 bg-paper/60 px-5 py-3 text-sm font-medium text-ink/80 transition hover:bg-paper hover:text-ink"
                  >
                    Send another
                  </button>
                </div>
              ) : (
                <form
                  className="space-y-5"
                  onSubmit={(e) => {
                    e.preventDefault()
                    if (!valid) return
                    const subject = encodeURIComponent(`Blueprint Reader inquiry — ${name}`)
                    const body = encodeURIComponent(
                      `Name: ${name}\nEmail: ${fromEmail}\n\n${message}\n`,
                    )
                    window.location.href = `mailto:${email}?subject=${subject}&body=${body}`
                    setSubmitted(true)
                  }}
                >
                  <div className="grid gap-4 md:grid-cols-2">
                    <label className="space-y-2">
                      <div className="text-xs tracking-[0.2em] text-ink/55">NAME</div>
                      <input
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        className="h-12 w-full rounded-2xl border border-ink/12 bg-paper/60 px-4 text-sm text-ink placeholder:text-ink/35 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50"
                        placeholder="Your name"
                      />
                    </label>
                    <label className="space-y-2">
                      <div className="text-xs tracking-[0.2em] text-ink/55">EMAIL</div>
                      <input
                        value={fromEmail}
                        onChange={(e) => setFromEmail(e.target.value)}
                        className="h-12 w-full rounded-2xl border border-ink/12 bg-paper/60 px-4 text-sm text-ink placeholder:text-ink/35 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50"
                        placeholder="name@company.com"
                      />
                    </label>
                  </div>

                  <label className="space-y-2">
                    <div className="text-xs tracking-[0.2em] text-ink/55">MESSAGE</div>
                    <textarea
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      className="min-h-[160px] w-full resize-none rounded-2xl border border-ink/12 bg-paper/60 px-4 py-3 text-sm leading-relaxed text-ink placeholder:text-ink/35 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50"
                      placeholder="Tell us what you’re trying to extract (rooms/areas/BOQ), what formats you use, and what you want the output to look like."
                    />
                  </label>

                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <button
                      type="submit"
                      disabled={!valid}
                      className={cn(
                        'inline-flex items-center justify-center rounded-full px-5 py-3 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50',
                        valid
                          ? 'bg-ink text-paper hover:-translate-y-px hover:bg-ink/90'
                          : 'cursor-not-allowed border border-ink/10 bg-paper-2/50 text-ink/40',
                      )}
                    >
                      Send message
                    </button>
                    <div className="text-xs text-ink/60">
                      This sends via your email client. No server required.
                    </div>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      </Container>
    </div>
  )
}

