# 📄 API Implementation & Frontend Handover Guide

This comprehensive document consolidates the implementation details and frontend integration guides/API contracts for the following features:
1.  **🎥 Video Generation API**
2.  **📱 Social Feed & Engagement API**
3.  **🤝 Follow/Unfollow & Personalized Feed**
4.  **💬 Chat System Implementation (Real-time)**

---

# 1. 🎥 Video Generation API

This feature enables users to generate videos from images using an asynchronous workflow initiated via GraphQL.

## Workflow Overview
1.  **Initiate Job**: Frontend sends an image + prompt -> Backend returns `jobId`.
2.  **Poll Status**: Frontend polls backend with `jobId`.
3.  **Display Result**: Once status is "completed", backend returns the video URL.

### 1.1 Start Video Generation
Call this mutation when the user clicks "Generate".

**Mutation:**
```graphql
mutation GenerateVideo($userId: String!, $prompt: String!, $image: Upload!) {
  generateImage(userId: $userId, prompt: $prompt, image: $image) {
    status
    message
    data {
      jobId          # <--- Save this for polling
      status         # Usually "processing"
      inputImageUrl  # Cloudflare URL of the uploaded image
    }
  }
}
```

**Success Response:**
```json
{
  "data": {
    "generateImage": {
      "status": true,
      "message": "Video generation job initiated successfully",
      "data": {
        "jobId": "job_abc123",
        "status": "processing",
        "inputImageUrl": "https://pub-xyz.r2.dev/dog.jpg"
      }
    }
  }
}
```

### 1.2 Check Status & Get Video
Poll this query every few seconds (e.g., 3000ms) until `status` is "completed".

**Query:**
```graphql
query CheckStatus($jobId: String!) {
  checkVideoStatus(jobId: $jobId) {
    status
    message
    data {
      jobId
      status     # "processing" | "completed" | "failed"
      videoUrl   # Null until status is "completed"
    }
  }
}
```

**Response (Completed):**
```json
{
  "data": {
    "checkVideoStatus": {
      "status": true,
      "data": {
        "jobId": "job_abc123",
        "status": "completed",
        "videoUrl": "https://revid.ai/video/final_roast.mp4"
      }
    }
  }
}
```

---

# 2. 📱 Social Feed & Engagement API

Features: Publishing Posts, Viewing Feed, Likes, Comments, Notifications.

### 2.1 Create Post (Publish Video)
Publish the generated video to the community feed.

**Mutation:**
```graphql
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    status
    data {
      _id
      contentUrl
      caption
      type
    }
  }
}
```

**Variables:**
```json
{
  "input": {
    "userId": "user_123",
    "contentUrl": "https://revid.ai/video/final_roast.mp4",
    "type": "video",
    "caption": "My dog getting roasted!"
  }
}
```

### 2.2 Like / Unlike Post
Toggles the like status.

**Mutation:**
```graphql
mutation ToggleLike($userId: String!, $postId: String!) {
  toggleLike(userId: $userId, postId: $postId) {
    status
    data {
      isLiked    # New state (true/false)
      stats {
        likeCount  # Updated count
      }
    }
  }
}
```

### 2.3 Add Comment
**Mutation:**
```graphql
mutation AddComment($userId: String!, $postId: String!, $text: String!) {
  addComment(userId: $userId, postId: $postId, text: $text) {
    status
    data {
      _id
      text
      createdAt
    }
  }
}
```

### 2.4 Get Notifications
Fetches recent activity (who liked/commented).

**Query:**
```graphql
query GetNotifications($userId: String!, $limit: Int, $offset: Int) {
  getNotifications(userId: $userId, limit: $limit, offset: $offset) {
    status
    data {
      actorId    # Who performed the action
      type       # "LIKE" or "COMMENT"
      entityId   # Post ID
      isRead
    }
  }
}
```

---

# 3. 🤝 Follow/Unfollow & Personalized Feed

### 3.1 Overview
The **Home Feed** (`getFeed`) is now **Personalized**.
*   **Behavior**: It automatically filters posts to show only content from:
    1.  Users the current user follows.
    2.  The current user themselves.
*   **Empty State**: If a user follows no one, the feed will only show their own posts (or be empty).

### 3.2 Follow a User
**Mutation:**
```graphql
mutation FollowUser($targetUserId: String!) {
  followUser(targetUserId: $targetUserId) {
    status
    message
  }
}
```

### 3.3 Unfollow a User
**Mutation:**
```graphql
mutation UnfollowUser($targetUserId: String!) {
  unfollowUser(targetUserId: $targetUserId) {
    status
    message
  }
}
```

### 3.4 Get Feed (Personalized)
**Query (Same as before, but filtered logic is applied backend-side):**
```graphql
query GetFeed($userId: String!, $limit: Int, $offset: Int) {
  getFeed(userId: $userId, limit: $limit, offset: $offset) {
    status
    data {
      _id
      userId
      contentUrl
      caption
      type
      isLikedByMe
    }
  }
}
```

---

# 4. 💬 Chat System Implementation

Real-time messaging between two users using GraphQL (for history/actions) and Socket.io (for live updates).

### 4.1 Prerequisites
*   Ensure **Socket.io** client is connected using the user's token.
*   **Socket URL**: (Your Backend URL)

### 4.2 Get Conversation List
Fetch list of active chats for the "Messages" tab.

**Query:**
```graphql
query GetUserConversations($userId: String!, $page: Int, $limit: Int) {
  getUserConversations(userId: $userId, page: $page, limit: $limit) {
    conversations {
      id
      participant1Id
      participant2Id
      lastMessagePreview
      unreadCount
    }
  }
}
```

### 4.3 Get Message History
Load messages when entering a chat.

**Query:**
```graphql
query GetConversationMessages($conversationId: String!, $page: Int, $limit: Int) {
  getConversationMessages(conversationId: $conversationId, page: $page, limit: $limit) {
    messages {
      id
      senderId
      content
      isRead
      createdAt
    }
  }
}
```

### 4.4 Send Message
Persist message to DB (Socket automatically notifies recipient).

**Mutation:**
```graphql
mutation SendMessage($userId: String!, $input: SendMessageInput!) {
  sendMessage(userId: $userId, input: $input) {
    id
    content
    createdAt
  }
}
```

**Input Variables:**
```json
{
  "userId": "UserA_ID",
  "input": {
    "receiverId": "UserB_ID",
    "messageType": "text", 
    "content": "Hello world"
  }
}
```

### 4.5 Real-time Updates (Frontend Listeners)

**New Message:**
```javascript
socket.on("new_message", (message) => {
  if (message.conversationId === currentActiveChatId) {
    appendMessageToUI(message);
  } else {
    showNotificationBadge();
  }
});
```

**Message Read Receipt:**
```javascript
socket.on("messages_read", (payload) => {
  // payload.messageIds contains IDs of messages read by the other user
  // Update those messages to "Blue Ticks" in UI
});
```

### 4.6 Mark as Read
Call this when User B opens the chat screen.

**Mutation:**
```graphql
mutation MarkMessagesAsRead($userId: String!, $messageIds: [String!]!) {
  markMessagesAsRead(userId: $userId, messageIds: $messageIds)
}
```

## **Summary of Chat Flow**

1.  **User A** -> `getUserConversations` -> Lists chats.
2.  **User A** -> `getConversationMessages` -> Loads chat logic.
3.  **User A** -> `sendMessage` -> Optimistically adds to UI + Sends to Server.
4.  **User B** -> `socket.on("new_message")` -> Sees "Hello".
5.  **User B** -> `markMessagesAsRead` -> Confirming view.
6.  **User A** -> `socket.on("messages_read")` -> Updates UI to "Read".
