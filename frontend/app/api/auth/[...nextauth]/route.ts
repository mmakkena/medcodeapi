import NextAuth, { NextAuthOptions } from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import AzureADProvider from "next-auth/providers/azure-ad";
import CredentialsProvider from "next-auth/providers/credentials";
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID || "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
    }),
    AzureADProvider({
      clientId: process.env.AZURE_AD_CLIENT_ID || "",
      clientSecret: process.env.AZURE_AD_CLIENT_SECRET || "",
      tenantId: process.env.AZURE_AD_TENANT_ID || "common",
    }),
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        try {
          const response = await axios.post(`${API_URL}/api/v1/auth/login`, {
            email: credentials.email,
            password: credentials.password,
          });

          if (response.data.access_token) {
            // Fetch user details
            const userResponse = await axios.get(`${API_URL}/api/v1/auth/me`, {
              headers: {
                Authorization: `Bearer ${response.data.access_token}`,
              },
            });

            return {
              id: userResponse.data.id,
              email: userResponse.data.email,
              accessToken: response.data.access_token,
            };
          }
          return null;
        } catch (error) {
          console.error("Login error:", error);
          return null;
        }
      },
    }),
  ],
  callbacks: {
    async signIn({ user, account, profile }) {
      // Handle OAuth sign-in (Google/Microsoft)
      if (account?.provider === "google" || account?.provider === "azure-ad") {
        try {
          // Check if user exists in our backend, if not create them
          const response = await axios.post(`${API_URL}/api/v1/auth/oauth/signin`, {
            email: user.email,
            provider: account.provider,
            providerId: account.providerAccountId,
            name: user.name,
          });

          // Store the backend access token
          user.accessToken = response.data.access_token;
          user.id = response.data.user.id;

          return true;
        } catch (error: any) {
          console.error("OAuth sign-in error:", error.response?.data || error.message);
          return false;
        }
      }
      return true;
    },
    async jwt({ token, user, account }) {
      // Initial sign in
      if (user && user.accessToken) {
        token.accessToken = user.accessToken;
        token.id = user.id;
      }
      return token;
    },
    async session({ session, token }) {
      // Send properties to the client
      if (token) {
        session.user.id = token.id as string;
        session.accessToken = token.accessToken as string;
      }
      return session;
    },
  },
  pages: {
    signIn: '/login',
    error: '/login',
  },
  session: {
    strategy: "jwt",
  },
  secret: process.env.NEXTAUTH_SECRET,
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
