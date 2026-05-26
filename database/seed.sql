-- Dados de exemplo - Sistema de Chamados - Colégio Mauá
-- Executado automaticamente pela aplicação

-- Setores
INSERT INTO setores (nome, descricao, ativo) VALUES
('TI - Tecnologia da Informação', 'Suporte técnico e infraestrutura de TI', 1),
('Manutenção', 'Manutenção predial e equipamentos', 1),
('Limpeza', 'Serviços de limpeza e conservação', 1),
('Segurança', 'Segurança patrimonial e vigilância', 1),
('Administrativo', 'Gestão administrativa e recursos humanos', 1),
('Pedagógico', 'Coordenação pedagógica e acadêmica', 1),
('Biblioteca', 'Biblioteca e acervo', 1),
('Almoxarifado', 'Controle de estoque e suprimentos', 1);

-- Usuários (senhas hasheadas com bcrypt - 'admin123' e '123456')
INSERT INTO usuarios (nome, email, senha_hash, perfil, ativo, setor_id) VALUES
('Administrador', 'admin@colegiomaua.edu.br', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYA.qGZvKG6', 'admin', 1, NULL),
('João Silva', 'joao@colegiomaua.edu.br', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYA.qGZvKG6', 'setor', 1, 1),
('Maria Oliveira', 'maria@colegiomaua.edu.br', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYA.qGZvKG6', 'setor', 1, 2),
('Carlos Santos', 'carlos@colegiomaua.edu.br', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYA.qGZvKG6', 'usuario', 1, NULL),
('Ana Pereira', 'ana@colegiomaua.edu.br', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYA.qGZvKG6', 'usuario', 1, NULL),
('Pedro Costa', 'pedro@colegiomaua.edu.br', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYA.qGZvKG6', 'usuario', 1, NULL),
('Fernanda Lima', 'fernanda@colegiomaua.edu.br', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYA.qGZvKG6', 'setor', 1, 3),
('Ricardo Souza', 'ricardo@colegiomaua.edu.br', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYA.qGZvKG6', 'usuario', 1, NULL),
('Juliana Martins', 'juliana@colegiomaua.edu.br', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYA.qGZvKG6', 'usuario', 1, NULL);
