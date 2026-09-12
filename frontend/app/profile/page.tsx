import { RequireAuth } from "@/components/auth/require-auth";
import { SectionShell } from "@/components/layout/section-shell";
import { ProfileForm } from "@/components/profile/profile-form";

export default function ProfilePage() {
  return (
    <RequireAuth>
      <SectionShell title="Votre profil" subtitle="Gérez votre identité et l’apparence de Kozons">
        <ProfileForm />
      </SectionShell>
    </RequireAuth>
  );
}
