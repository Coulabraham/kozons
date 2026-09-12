import { RequireAuth } from "@/components/auth/require-auth";
import { GroupCreateForm } from "@/components/groups/group-create-form";
import { SectionShell } from "@/components/layout/section-shell";

export default function NewGroupPage() {
  return (
    <RequireAuth>
      <SectionShell title="Nouveau groupe" subtitle="Choisissez les membres et donnez un nom au groupe">
        <GroupCreateForm />
      </SectionShell>
    </RequireAuth>
  );
}
