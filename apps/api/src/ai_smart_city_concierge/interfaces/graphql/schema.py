# Optional GraphQL Schema (Strawberry)
# Provides flexible queries as an alternative to REST.
#
# This is a placeholder for future GraphQL support.
# The REST API is the primary interface.

GRAPHQL_AVAILABLE = False

# Example schema (when implemented):
# type Query {
#   conversation(id: ID!): Conversation
#   conversations(first: Int, after: String): ConversationConnection
#   itinerary(id: ID!): Itinerary
#   poisNearby(lat: Float!, lng: Float!, radius: Int): [POI]
#   me: User
# }
#
# type Mutation {
#   startConversation(input: StartConversationInput!): Conversation!
#   sendMessage(conversationId: ID!, content: String!): Message!
# }
#
# type Subscription {
#   messageReceived(conversationId: ID!): Message!
# }
