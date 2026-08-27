interface FieldErrorProps {
  id: string
  message?: string
}

/** Inline per-field validation message, shown under a form control -
 * distinct from ErrorMessage (which reports a whole failed API call).
 * `role="alert"` announces it to screen readers the moment it appears;
 * pair the field with `aria-describedby={id}` and `aria-invalid` so
 * assistive tech associates the two even when not freshly announced. */
export function FieldError({ id, message }: FieldErrorProps) {
  if (!message) return null
  return (
    <p id={id} role="alert" className="mt-1 text-xs text-red-700">
      {message}
    </p>
  )
}
