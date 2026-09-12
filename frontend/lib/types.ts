export type UserStatus = "actif" | "inactif" | "suspendu";

export interface User {
  id: number;
  telephone: string | null;
  email: string | null;
  nom_affichage: string;
  avatar_url: string | null;
  statut: UserStatus;
  statut_personnalise?: string;
  date_creation?: string;
}

export interface Membership {
  id: number;
  utilisateur: User;
  role: "admin" | "membre";
  date_ajout: string;
}

export type MessageType = "texte" | "note_vocale" | "image" | "video";
export type ReceiptStatus = "envoye" | "recu" | "lu";

export interface MessageReceipt {
  user_id: number;
  statut: ReceiptStatus;
  date_maj: string;
}

export interface MessageReaction {
  user_id: number;
  emoji: string;
}

export interface Message {
  id: number;
  client_id: string | null;
  conversation_id: number;
  sender_id: number;
  type: MessageType;
  contenu: string | null;
  media_url: string | null;
  duree: number | null;
  date_envoi: string;
  modifie_le: string | null;
  supprime_pour_tous_le: string | null;
  transfere: boolean;
  receipts: MessageReceipt[];
  reactions: MessageReaction[];
  pending?: boolean;
}

export interface Conversation {
  id: number;
  type: "individuel" | "groupe";
  nom: string | null;
  avatar_url: string | null;
  envoi_messages: "tous" | "admins";
  date_creation: string;
  membres: Membership[];
  last_message?: Message | null;
  unread_count?: number;
}

export interface GlobalSearchResults {
  conversations: Conversation[];
  contacts: User[];
}

export interface CursorPage<T> {
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface MediaAsset {
  id: number;
  conversation_id: number | null;
  type: Exclude<MessageType, "texte">;
  statut: "en_attente" | "uploade" | "traitement" | "pret" | "echec";
  content_type: string;
  taille_octets: number;
  duree: number | null;
  date_creation: string;
}

export interface PresignResponse {
  asset: MediaAsset;
  upload: { url: string; fields: Record<string, string> };
}

export interface ProcessedMedia {
  id: number;
  type: Exclude<MessageType, "texte">;
  status: MediaAsset["statut"];
  download_url: string;
  thumbnail_url: string | null;
  duration: number | null;
}
