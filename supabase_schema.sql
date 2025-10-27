-- Script SQL pour créer les tables dans Supabase
-- Exécutez ce script dans l'éditeur SQL de votre tableau de bord Supabase

-- Table des utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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

-- Activer Row Level Security (RLS) - optionnel mais recommandé
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Politiques RLS pour permettre toutes les opérations (à adapter selon vos besoins de sécurité)
-- Ces politiques permettent l'accès complet pour l'instant. 
-- En production, vous devriez les ajuster selon vos besoins.

CREATE POLICY "Permettre toutes les opérations sur users" 
    ON users FOR ALL 
    USING (true) 
    WITH CHECK (true);

CREATE POLICY "Permettre toutes les opérations sur conversations" 
    ON conversations FOR ALL 
    USING (true) 
    WITH CHECK (true);

CREATE POLICY "Permettre toutes les opérations sur messages" 
    ON messages FOR ALL 
    USING (true) 
    WITH CHECK (true);

