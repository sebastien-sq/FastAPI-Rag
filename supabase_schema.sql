-- Script SQL pour créer les tables dans Supabase
-- Exécutez ce script dans l'éditeur SQL de votre tableau de bord Supabase

-- Table des utilisateurs (username contient l'email)
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL, -- Email de l'utilisateur
    auth_user_id UUID UNIQUE, -- Lien avec l'utilisateur Supabase Auth
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT email_format CHECK (username ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Table des conversations
CREATE TABLE IF NOT EXISTS conversations (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table des messages
CREATE TABLE IF NOT EXISTS messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_auth_user_id ON users(auth_user_id);

-- Activer Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Supprimer les anciennes politiques si elles existent
DROP POLICY IF EXISTS "Permettre toutes les opérations sur users" ON users;
DROP POLICY IF EXISTS "Permettre toutes les opérations sur conversations" ON conversations;
DROP POLICY IF EXISTS "Permettre toutes les opérations sur messages" ON messages;

-- Politiques RLS pour les utilisateurs
-- Les utilisateurs peuvent lire et mettre à jour leur propre profil
CREATE POLICY "Les utilisateurs peuvent lire leur propre profil" 
    ON users FOR SELECT 
    USING (auth.uid() = auth_user_id);

CREATE POLICY "Les utilisateurs peuvent mettre à jour leur propre profil" 
    ON users FOR UPDATE 
    USING (auth.uid() = auth_user_id);

-- Permettre l'insertion lors de l'inscription (via service_role ou anon)
CREATE POLICY "Permettre l'insertion des nouveaux utilisateurs" 
    ON users FOR INSERT 
    WITH CHECK (true);

-- Politiques RLS pour les conversations
-- Les utilisateurs peuvent uniquement voir leurs propres conversations
CREATE POLICY "Les utilisateurs peuvent voir leurs propres conversations" 
    ON conversations FOR SELECT 
    USING (
        user_id IN (
            SELECT id FROM users WHERE auth_user_id = auth.uid()
        )
    );

CREATE POLICY "Les utilisateurs peuvent créer leurs propres conversations" 
    ON conversations FOR INSERT 
    WITH CHECK (
        user_id IN (
            SELECT id FROM users WHERE auth_user_id = auth.uid()
        )
    );

CREATE POLICY "Les utilisateurs peuvent supprimer leurs propres conversations" 
    ON conversations FOR DELETE 
    USING (
        user_id IN (
            SELECT id FROM users WHERE auth_user_id = auth.uid()
        )
    );

-- Politiques RLS pour les messages
-- Les utilisateurs peuvent voir les messages de leurs propres conversations
CREATE POLICY "Les utilisateurs peuvent voir les messages de leurs conversations" 
    ON messages FOR SELECT 
    USING (
        conversation_id IN (
            SELECT c.id 
            FROM conversations c 
            INNER JOIN users u ON c.user_id = u.id 
            WHERE u.auth_user_id = auth.uid()
        )
    );

CREATE POLICY "Les utilisateurs peuvent créer des messages dans leurs conversations" 
    ON messages FOR INSERT 
    WITH CHECK (
        conversation_id IN (
            SELECT c.id 
            FROM conversations c 
            INNER JOIN users u ON c.user_id = u.id 
            WHERE u.auth_user_id = auth.uid()
        )
    );

CREATE POLICY "Les utilisateurs peuvent supprimer les messages de leurs conversations" 
    ON messages FOR DELETE 
    USING (
        conversation_id IN (
            SELECT c.id 
            FROM conversations c 
            INNER JOIN users u ON c.user_id = u.id 
            WHERE u.auth_user_id = auth.uid()
        )
    );

