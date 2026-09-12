import { RequireAuth } from "@/components/auth/require-auth";
import { ContactsScreen } from "@/components/contacts/contacts-screen";
import { SectionShell } from "@/components/layout/section-shell";

export default function ContactsPage() {
  return (
    <RequireAuth>
      <SectionShell title="Contacts" subtitle="Les personnes de votre carnet déjà sur Kozons">
        <ContactsScreen />
      </SectionShell>
    </RequireAuth>
  );
}
