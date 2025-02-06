import { NextAuthOptions, DefaultSession } from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import CredentialsProvider from "next-auth/providers/credentials";
import { connectDB, client } from "./mongodb";

declare module "next-auth" {
  interface Session {
    user?: DefaultSession["user"] & {
      id: string
    }
  }
}

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID ?? "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET ?? "",
    }),
    CredentialsProvider({
      id: 'temporary',
      name: 'Temporary User',
      credentials: {},
      async authorize() {
        const user = {
          id: `temp_${Date.now()}`,
          name: `Temporary User`,
          email: `temp_${Date.now()}@temporary.user`,
        };
        return user;
      },
    }),
  ],
  pages: {
    signIn: "/auth/signin",
    error: "/auth/error",
  },
  callbacks: {
    async signIn({ user, account }) {
      if (account?.provider === "google") {
        try {
          const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
          if (!backendUrl) {
            console.error("Backend URL is not configured");
            return false;
          }
          const response = await fetch(
            `${backendUrl}/add_user`,
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify(user),
            }
          )
          console.log("add_user response: ", response);
          if (!response.ok) {
            console.error("Failed to add user");
            return false;
          }
          return true;
          
          // await connectDB();
          // const db = client.db();

          // // Check if user exists
          // const existingUser = await db.collection('users').findOne({ email: user.email });

          // if (!existingUser) {
          //   try {
          //     // Attempt to create new user
          //     await db.collection('users').insertOne({
          //       name: user.name,
          //       email: user.email,
          //       image: user.image,
          //       googleId: user.id,
          //       createdAt: new Date(),
          //     });              
          //   } catch (dbError) {
          //     console.error("Failed to create user in database:", dbError);
          //     return false;
          //   }
          // }

          return true;
        } catch (error) {
          console.error("Error during sign in:", error);
          return false;
        }
      }        
      return true;
    },
    async session({ session, token }) {      
      if (session.user) {
        session.user.id = token.sub!;
      }
      return session;
    },
    async jwt({ token }) {
      return token;
    },
  },
};