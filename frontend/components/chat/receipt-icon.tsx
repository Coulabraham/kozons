import { CheckDoubleIcon, CheckIcon } from "@/components/ui/icons";
import type { MessageReceipt } from "@/lib/types";

export function ReceiptIcon({ receipts, pending }: { receipts: MessageReceipt[]; pending?: boolean }) {
  if (pending) {
    return <span role="img" className="h-2 w-2 animate-soft-pulse rounded-full bg-current" aria-label="Envoi en cours" />;
  }
  const read = receipts.some((receipt) => receipt.statut === "lu");
  const delivered = receipts.some((receipt) => receipt.statut === "recu");
  const label = read ? "Lu" : delivered ? "Reçu" : "Envoyé";
  return (
    <span role="img" aria-label={label}>
      {read || delivered ? (
        <CheckDoubleIcon size={15} className={read ? "text-brand-600 dark:text-brand-400" : ""} />
      ) : (
        <CheckIcon size={15} />
      )}
    </span>
  );
}
