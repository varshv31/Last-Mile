import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { AddressInput } from "@/lib/api-types";

export const EMPTY_ADDRESS: AddressInput = {
  name: "",
  phone: "",
  address_line1: "",
  address_line2: "",
  city: "",
  state: "",
  postal_code: "",
  country: "India",
};

export function Field({
  id,
  label,
  children,
  hint,
  className,
}: {
  id?: string;
  label: string;
  children: React.ReactNode;
  hint?: string;
  className?: string;
}) {
  return (
    <div className={className}>
      <Label htmlFor={id} className="mb-1.5 block text-xs font-medium text-muted-foreground">
        {label}
      </Label>
      {children}
      {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  );
}

export function AddressFields({
  idPrefix,
  value,
  onChange,
  disabled,
}: {
  idPrefix: string;
  value: AddressInput;
  onChange: (next: AddressInput) => void;
  disabled?: boolean;
}) {
  const set = (patch: Partial<AddressInput>) => onChange({ ...value, ...patch });

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <Field id={`${idPrefix}-name`} label="Contact name">
        <Input
          id={`${idPrefix}-name`}
          value={value.name}
          disabled={disabled ?? false}
          onChange={(e) => set({ name: e.target.value })}
          placeholder="Full name"
          required
        />
      </Field>
      <Field id={`${idPrefix}-phone`} label="Phone">
        <Input
          id={`${idPrefix}-phone`}
          value={value.phone}
          disabled={disabled ?? false}
          onChange={(e) => set({ phone: e.target.value })}
          placeholder="9876543210"
          inputMode="tel"
          required
        />
      </Field>
      <Field id={`${idPrefix}-line1`} label="Address line 1" className="sm:col-span-2">
        <Input
          id={`${idPrefix}-line1`}
          value={value.address_line1}
          disabled={disabled ?? false}
          onChange={(e) => set({ address_line1: e.target.value })}
          placeholder="Street, building"
          required
        />
      </Field>
      <Field id={`${idPrefix}-line2`} label="Address line 2 (optional)" className="sm:col-span-2">
        <Input
          id={`${idPrefix}-line2`}
          value={value.address_line2 ?? ""}
          disabled={disabled ?? false}
          onChange={(e) => set({ address_line2: e.target.value })}
          placeholder="Landmark, area"
        />
      </Field>
      <Field id={`${idPrefix}-city`} label="City">
        <Input
          id={`${idPrefix}-city`}
          value={value.city}
          disabled={disabled ?? false}
          onChange={(e) => set({ city: e.target.value })}
          required
        />
      </Field>
      <Field id={`${idPrefix}-state`} label="State">
        <Input
          id={`${idPrefix}-state`}
          value={value.state}
          disabled={disabled ?? false}
          onChange={(e) => set({ state: e.target.value })}
          required
        />
      </Field>
      <Field
        id={`${idPrefix}-postal`}
        label="Postal code"
        hint="Must map to a configured service area."
      >
        <Input
          id={`${idPrefix}-postal`}
          value={value.postal_code}
          disabled={disabled ?? false}
          onChange={(e) => set({ postal_code: e.target.value })}
          inputMode="numeric"
          required
        />
      </Field>
      <Field id={`${idPrefix}-country`} label="Country">
        <Input
          id={`${idPrefix}-country`}
          value={value.country ?? ""}
          disabled={disabled ?? false}
          onChange={(e) => set({ country: e.target.value })}
        />
      </Field>
    </div>
  );
}

export function addressComplete(a: AddressInput): boolean {
  return Boolean(
    a.name.trim() &&
      a.phone.trim() &&
      a.address_line1.trim() &&
      a.city.trim() &&
      a.state.trim() &&
      a.postal_code.trim(),
  );
}
