"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { MobileNav } from "@/components/navigation/mobile-nav";
import { NotificationPrompt } from "@/components/notifications/notification-prompt";
import { ChatIcon } from "@/components/ui/icons";
import {
  useConversationMessages,
  useDeleteMessage,
  useEditMessage,
  useForwardMessage,
  useGlobalSearch,
  useLeaveConversation,
  useMediaUpload,
  useMessageReaction,
  useMessageSearch,
  useRemoveGroupMember,
  useSetGroupMemberRole,
  useUpdateGroup,
} from "@/lib/api/hooks";
import { useConversationRealtime } from "@/lib/realtime/use-conversation-realtime";
import { useUserRealtime } from "@/lib/realtime/use-user-realtime";
import type { Message, MessageType } from "@/lib/types";
import { useChatTools } from "@/lib/webmcp/use-chat-tools";
import { useAuthStore } from "@/store/auth-store";
import { useChatStore } from "@/store/chat-store";

import { ChatHeader } from "./chat-header";
import { Composer } from "./composer";
import { ConversationList } from "./conversation-list";
import { InfoPanel } from "./info-panel";
import { MessageThread } from "./message-thread";

function mutationError(error: unknown) {
  window.alert(error instanceof Error ? error.message : "L’action a échoué.");
}

export function ChatShell() {
  const authenticatedUser = useAuthStore((state) => state.user);
  const currentUserId = authenticatedUser?.id ?? 0;
  const conversations = useChatStore((state) => state.conversations);
  const messagesByConversation = useChatStore((state) => state.messages);
  const presence = useChatStore((state) => state.presence);
  const typing = useChatStore((state) => state.typing);
  const activeId = useChatStore((state) => state.activeConversationId);
  const mobileView = useChatStore((state) => state.mobileView);
  const infoPanelOpen = useChatStore((state) => state.infoPanelOpen);
  const openConversation = useChatStore((state) => state.openConversation);
  const showConversationList = useChatStore((state) => state.showConversationList);
  const toggleInfoPanel = useChatStore((state) => state.toggleInfoPanel);
  const removeConversation = useChatStore((state) => state.removeConversation);
  const upsertMessage = useChatStore((state) => state.upsertMessage);
  const [conversationSearch, setConversationSearch] = useState("");
  const [messageSearchOpen, setMessageSearchOpen] = useState(false);
  const [messageSearch, setMessageSearch] = useState("");
  const [searchIndex, setSearchIndex] = useState(0);
  const active = useMemo(() => conversations.find((item) => item.id === activeId) ?? null, [activeId, conversations]);
  const messages = activeId ? messagesByConversation[activeId] ?? [] : [];
  const messageQuery = useConversationMessages(activeId);
  const globalSearchQuery = useGlobalSearch(conversationSearch);
  const messageSearchQuery = useMessageSearch(activeId, messageSearch);
  const realtime = useConversationRealtime(activeId);
  useUserRealtime();
  const mediaUpload = useMediaUpload();
  const leaveConversation = useLeaveConversation();
  const editMessage = useEditMessage();
  const deleteMessage = useDeleteMessage();
  const forwardMessage = useForwardMessage();
  const messageReaction = useMessageReaction();
  const updateGroup = useUpdateGroup();
  const removeGroupMember = useRemoveGroupMember();
  const setGroupMemberRole = useSetGroupMemberRole();
  const searchResults = messageSearchQuery.data ?? [];
  const activeSearchResultId = searchResults.length ? searchResults[Math.min(searchIndex, searchResults.length - 1)]?.id ?? null : null;
  const currentMembership = active?.membres.find((member) => member.utilisateur.id === currentUserId);
  const composerDisabled = Boolean(active?.type === "groupe" && active.envoi_messages === "admins" && currentMembership?.role !== "admin");
  const adminActionPending = updateGroup.isPending || removeGroupMember.isPending || setGroupMemberRole.isPending || mediaUpload.isPending;
  const sendText = useCallback(
    (text: string) => realtime.sendMessage({ messageType: "texte", contenu: text }),
    [realtime.sendMessage],
  );
  useChatTools(conversations, activeId, sendText);

  useEffect(() => {
    setMessageSearch("");
    setMessageSearchOpen(false);
    setSearchIndex(0);
  }, [activeId]);
  useEffect(() => {
    setSearchIndex(0);
  }, [messageSearch]);
  useEffect(() => {
    messageSearchQuery.data?.forEach(upsertMessage);
  }, [messageSearchQuery.data, upsertMessage]);
  useEffect(() => {
    if (!active || !messages.length) return;
    const lastIncoming = [...messages].reverse().find((message) => message.sender_id !== currentUserId && message.id > 0);
    if (lastIncoming) realtime.sendReceipt(lastIncoming.id, "lu");
  }, [active, currentUserId, messages, realtime.sendReceipt]);

  const uploadAndSend = async (file: File, type: Exclude<MessageType, "texte">, duration?: number) => {
    if (!activeId || !authenticatedUser) return;
    try {
      const asset = await mediaUpload.mutateAsync({ file, conversationId: activeId, type });
      realtime.sendMessage({ messageType: type, mediaAssetId: asset.id, duree: duration });
    } catch (error) {
      mutationError(error);
    }
  };
  const leave = () => {
    if (!active || !authenticatedUser) return;
    leaveConversation.mutate(active.id, { onSuccess: () => removeConversation(active.id), onError: mutationError });
  };
  const edit = (message: Message, contenu: string) => editMessage.mutate({ messageId: message.id, contenu }, { onError: mutationError });
  const remove = (message: Message, mode: "me" | "everyone") => deleteMessage.mutate({ message, mode }, { onError: mutationError });
  const forward = (message: Message, conversationIds: number[]) => forwardMessage.mutate({ messageId: message.id, conversationIds }, { onError: mutationError });
  const react = (message: Message, emoji: string) => messageReaction.mutate({ messageId: message.id, emoji }, { onError: mutationError });
  const changeGroup = (body: { nom?: string; avatar_media_id?: number | null; envoi_messages?: "tous" | "admins" }) => {
    if (!active) return;
    updateGroup.mutate({ conversationId: active.id, ...body }, { onError: mutationError });
  };
  const changeGroupPhoto = async (file: File) => {
    if (!active) return;
    try {
      const asset = await mediaUpload.mutateAsync({ file, type: "image" });
      changeGroup({ avatar_media_id: asset.id });
    } catch (error) {
      mutationError(error);
    }
  };

  return (
    <main className="flex h-dvh overflow-hidden bg-canvas">
      <div className={`${mobileView === "conversation" ? "hidden lg:flex" : "flex"} h-full w-full flex-col lg:w-auto`}>
        <ConversationList conversations={conversations} currentUserId={currentUserId} activeId={activeId} presence={presence} search={conversationSearch} searchResults={globalSearchQuery.data} searching={globalSearchQuery.isFetching} onSearchChange={setConversationSearch} onOpen={openConversation} />
        <MobileNav />
      </div>
      <section className={`${mobileView === "conversation" ? "flex" : "hidden lg:flex"} relative min-w-0 flex-1 flex-col`}>
        {active ? <><ChatHeader conversation={active} currentUserId={currentUserId} presence={presence} connected={realtime.connected} searchQuery={messageSearch} searchOpen={messageSearchOpen} resultCount={searchResults.length} resultIndex={searchIndex} onSearchOpen={setMessageSearchOpen} onSearchChange={setMessageSearch} onPreviousResult={() => setSearchIndex((index) => searchResults.length ? (index - 1 + searchResults.length) % searchResults.length : 0)} onNextResult={() => setSearchIndex((index) => searchResults.length ? (index + 1) % searchResults.length : 0)} onBack={showConversationList} onInfo={toggleInfoPanel} /><NotificationPrompt /><MessageThread conversation={active} conversations={conversations} messages={messages} currentUserId={currentUserId} typingUserIds={typing[active.id] ?? []} hasOlder={Boolean(messageQuery.hasNextPage)} loadingOlder={messageQuery.isFetchingNextPage} searchTerm={messageSearch} activeSearchResultId={activeSearchResultId} onLoadOlder={() => messageQuery.fetchNextPage()} onEdit={edit} onDelete={remove} onForward={forward} onReact={react} /><Composer disabled={composerDisabled} uploading={mediaUpload.isPending} onSendText={(contenu) => realtime.sendMessage({ messageType: "texte", contenu })} onTyping={realtime.sendTyping} onAttachment={(file, type) => uploadAndSend(file, type)} onVoice={(file, duration) => uploadAndSend(file, "note_vocale", duration)} /></> : <div className="chat-pattern grid h-full place-items-center p-8 text-center"><div><span className="mx-auto grid h-20 w-20 place-items-center rounded-[1.75rem] bg-brand-50 text-brand-600"><ChatIcon size={34} /></span><h1 className="mt-5 text-xl font-extrabold">Vos messages, simplement</h1><p className="mt-1 max-w-sm text-sm text-muted">Choisissez une discussion ou démarrez-en une nouvelle.</p></div></div>}
      </section>
      {active && infoPanelOpen && <InfoPanel conversation={active} messages={messages} currentUserId={currentUserId} leaving={leaveConversation.isPending} adminActionPending={adminActionPending} onClose={toggleInfoPanel} onLeave={leave} onRename={(nom) => changeGroup({ nom })} onGroupPhoto={changeGroupPhoto} onSendPermission={(envoi_messages) => changeGroup({ envoi_messages })} onRoleChange={(userId, role) => setGroupMemberRole.mutate({ conversationId: active.id, userId, role }, { onError: mutationError })} onRemoveMember={(userId) => removeGroupMember.mutate({ conversationId: active.id, userId }, { onError: mutationError })} />}
    </main>
  );
}
