import "reflect-metadata";
import { ApolloServer } from "apollo-server-express";
import express from "express";
import bodyParser from "body-parser";
import { createServer } from "http";
import { buildSchema } from "type-graphql";
import { UserResolver } from "./resolvers/UserResolver";
import { connectMongoDB } from "./config/mongodb";
import { AppDataSource } from "./config/postgres";
import { logger } from "./utils/logger";
import { authContext } from "./middleware/authContext";
import dotenv from "dotenv";
import { runAllSeeds } from "./seed";
import { initializeSocketServer } from "./socket/server";
import { ChatResolver } from "./resolvers/ChatResolver";
import { ChatMediaResolver } from "./resolvers/ChatMediaResolver";
import { ImageResolver } from "./resolvers/ImageResolver";
import { PostResolver } from "./resolvers/PostResolver";
import chatRoutes from "./routes/chatRoutes";
import chatMediaRoutes from "./routes/chatMediaRoutes";

dotenv.config();

async function bootstrap() {
  try {
    // ✅ Connect to MongoDB
    await connectMongoDB();

    // ✅ Initialize PostgreSQL only if not already connected
    if (!AppDataSource.isInitialized) {
      await AppDataSource.initialize();
      logger.info(`✅ PostgreSQL connected`);
    } else {
      logger.info(`ℹ️ PostgreSQL already initialized`);
    }

    // ✅ Build GraphQL schema
    const schema = await buildSchema({
      resolvers: [UserResolver, ChatResolver, ChatMediaResolver, ImageResolver, PostResolver],
    });

    const app = express();

    // ✅ Parse JSON for everything EXCEPT /graphql
    app.use((req, res, next) => {
      if (req.path === "/graphql") return next();
      bodyParser.json()(req, res, next);
    });

    // REST routes removed in favor of GraphQL
    // app.use("/api/chat", chatRoutes);
    // app.use("/api/chat", chatMediaRoutes);

    // ✅ Apollo Server setup
    const server = new ApolloServer({
      schema,
      introspection: true, // Allow GraphQL tools to load schema
      context: ({ req, res }) => authContext({ req, res }),
      persistedQueries: false
    });

    await server.start();
    // Disable built-in generic upload handling to favor our custom scalar or verify support
    server.applyMiddleware({ app });

    await runAllSeeds();

    // ✅ Create HTTP server for Socket.io
    const httpServer = createServer(app);

    // ✅ Initialize Socket.io
    initializeSocketServer(httpServer);

    const PORT = process.env.PORT || 4000;
    httpServer.listen(PORT, () => {
      logger.info(
        `🚀 GraphQL running at http://localhost:${PORT}${server.graphqlPath}`
      );
      logger.info(`✅ Chat REST API: http://localhost:${PORT}/api/chat`);
      logger.info(`✅ Socket.io server running on port ${PORT}`);
      logger.info("✅ Clerk webhook endpoint: POST /webhooks/clerk");
    });
  } catch (err) {
    logger.error("❌ Server bootstrap failed:", err);
    process.exit(1); // Exit if bootstrap fails
  }
}

bootstrap();
