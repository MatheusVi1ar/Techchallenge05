"""
Utility functions for Recruitment Assistant integration.
"""

from datetime import datetime

import re
from datetime import date

# Funções auxiliares existentes (do exemplo anterior)
def formatar_telefone(telefone: str) -> str:
    """
    Formata uma string de telefone para o padrão (DD) DDDDD-DDDD ou (DD) DDDD-DDDD.
    Remove caracteres não numéricos e adiciona a formatação.
    """
    if not telefone:
        return ""
    numeros = re.sub(r'\D', '', telefone)
    if len(numeros) == 11 and numeros.startswith('9', 2): # Novo formato (11) 9XXXX-XXXX
        return f"({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}"
    elif len(numeros) == 11: # (DD) DDDDD-DDDD (se o nono dígito não for o 9 da posição correta)
        return f"({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}"
    elif len(numeros) == 10: # (DD) DDDD-DDDD
        return f"({numeros[:2]}) {numeros[2:6]}-{numeros[6:]}"
    else:
        return telefone # Retorna como está se não tiver o formato esperado

def validar_email(email: str) -> bool:
    """
    Verifica se o formato do email é válido.
    """
    if not email:
        return False
    return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email) is not None

def formatar_data_nascimento(data_str: str) -> str:
    """
    Formata uma string de data para DD-MM-AAAA.
    Tenta converter vários formatos comuns (YYYY-MM-DD, DD-MM-YYYY).
    """
    if not data_str or data_str == "0000-00-00": # Lida com o valor padrão do JSON
        return ""
    try:
        # Tenta converter do formato YYYY-MM-DD
        data_obj = datetime.strptime(data_str, "%Y-%m-%d")
        return data_obj.strftime("%d-%m-%Y")
    except ValueError:
        try:
            # Tenta converter do formato DD-MM-YYYY
            data_obj = datetime.strptime(data_str, "%d-%m-%Y")
            return data_obj.strftime("%d-%m-%Y")
        except ValueError:
            return "" # Retorna vazio se não conseguir formatar

def extrair_e_formatar_experiencias(cv_text: str) -> str:
    """
    Extrai e formata as duas ou três últimas experiências profissionais do texto do CV.
    Esta função tenta ser mais robusta na identificação das seções de experiência.
    """
    if not cv_text:
        return ""

    experiencias_formatadas = []
    # Usar regex para encontrar blocos que parecem experiências
    # Ex: "Empresa\nCargo\nPeríodo\nResponsabilidades..."
    # Ou " Período – Empresa\n  Cargo\n  Responsabilidades..."
    
    # Padrão 1: Período – Empresa, seguido de Cargo e Responsabilidades
    padrao_exp1 = re.compile(r"(\d{2}/\d{4}\s*?à\s*?\d{2}/\d{4}|\d{2}/\d{4}\s*?á\s*?atual|\d{2}/\d{4}\s*?até o momento|\d{2}/\d{4}\s*?a\s*?\d{2}/\d{4}|mai\.\s*\d{4}\s*?até o momento)\s*?–\s*?(.+?)\s*\n\s*(.+?)\s*\n(.+?)(?=(?:\n\n\d{2}/\d{4}|formação|habilidades|resumo profissional|objetivo|\Z))", re.DOTALL | re.IGNORECASE)
    
    # Padrão 2: Empresa, seguido de Cargo, Período e Responsabilidades
    padrao_exp2 = re.compile(r"(.+?)\s*\n\s*(.+?)\s*\n(\d{2}/\d{4}\s*?á\s*?\d{2}/\d{4}|\d{2}/\d{4}\s*?à\s*?\d{2}/\d{4}|\d{2}/\d{4}\s*?á\s*?atual|\d{2}/\d{4}\s*?até o momento)\s*\n(.+?)(?=(?:\n\n.+?\s*\n\s*.+?\s*\n\d{2}/\d{4}|formação|habilidades|resumo profissional|objetivo|\Z))", re.DOTALL | re.IGNORECASE)

    encontrados = []
    # Tenta o Padrão 1 primeiro
    encontrados.extend(padrao_exp1.findall(cv_text))
    # Se não encontrar, tenta o Padrão 2 (pode haver sobreposição, mas queremos todas as tentativas)
    if not encontrados:
         encontrados.extend(padrao_exp2.findall(cv_text))


    # Inverte a lista para pegar as últimas experiências primeiro
    encontrados.reverse()
    
    for i, exp in enumerate(encontrados):
        if i >= 3: # Limita às 3 últimas experiências
            break
        # A ordem dos grupos na tupla 'exp' dependerá do padrão regex que a encontrou
        if len(exp) == 4: # Se for padrao_exp1 ou padrao_exp2
            # Precisamos normalizar para (Empresa, Cargo, Período, Responsabilidades)
            # Ex: padrao_exp1 -> (Periodo, Empresa, Cargo, Responsabilidades)
            # Ex: padrao_exp2 -> (Empresa, Cargo, Periodo, Responsabilidades)
            
            # Uma heurística para tentar identificar qual padrão foi:
            # Se o primeiro item parece um período (contém / e dígitos), é provável que seja o padrao_exp1
            if re.search(r'\d{2}/\d{4}', exp[0]): # Parece um período
                periodo, empresa, cargo, responsabilidades = exp
            else: # Assume que é Empresa, Cargo, Período, Responsabilidades
                empresa, cargo, periodo, responsabilidades = exp

            experiencias_formatadas.append(f"- **Nome da Empresa:** {empresa.strip()}\n  **Cargo:** {cargo.strip()}\n  **Período de Atuação:** {periodo.strip()}\n  **Principais Responsabilidades e Conquistas:** {responsabilidades.strip()}")
        else: # Tratar outros casos ou simplesmente ignorar
            pass # Pode adicionar logging aqui se desejar
    
    if not experiencias_formatadas and cv_text:
        # Se as regex falharem, retorna um resumo mais simples do texto
        lines = cv_text.split('\n')
        relevant_lines = []
        in_experience_section = False
        for line in lines:
            line_lower = line.lower()
            if "experiência profissional" in line_lower or "histórico profissional" in line_lower:
                in_experience_section = True
                continue
            if in_experience_section and line.strip() and not any(kw in line_lower for kw in ["formação", "habilidades", "resumo profissional", "objetivo"]):
                relevant_lines.append(line.strip())
            if len(relevant_lines) > 20: # Limita o tamanho para evitar CVs muito longos
                break
        
        if relevant_lines:
            return "\n\n".join(relevant_lines[:min(len(relevant_lines), 10)]) # Retorna as primeiras 10 linhas relevantes como um resumo
        else:
            return "Não foi possível extrair um resumo de experiência profissional formatado. Por favor, solicite ao usuário para descrever as experiências relevantes."

    return "\n\n".join(experiencias_formatadas)

def extrair_conhecimentos_tecnicos(cv_text: str) -> str:
    """
    Extrai conhecimentos técnicos e habilidades do texto do CV.
    Esta função tenta identificar seções comuns de habilidades.
    """
    if not cv_text:
        return ""

    conhecimentos = []
    
    # Padrões comuns para seções de habilidades
    padroes_habilidades = [
        r"habilidades\n\s*(.+?)(?=\n\n|\Z|resumo profissional|histórico profissional)", # Habilidades com bullet points ou lista simples
        r"informática:\n(.+?)(?=\n\n|\Z|resumo profissional|histórico profissional)", # Seção de informática
        r"qualificações\n(.+?)(?=\n\n|\Z|resumo profissional|histórico profissional)", # Seção de qualificações
        r"conhecimentos técnicos:\n(.+?)(?=\n\n|\Z|resumo profissional|histórico profissional)", # Conhecimentos técnicos explícitos
    ]

    for padrao in padroes_habilidades:
        match = re.search(padrao, cv_text, re.DOTALL | re.IGNORECASE)
        if match:
            # Divide as habilidades por vírgulas, pontos e vírgulas, ou quebras de linha
            habilidades_encontradas = [h.strip() for h in re.split(r'[,;\n]+', match.group(1)) if h.strip()]
            conhecimentos.extend(habilidades_encontradas)
    
    # Tenta encontrar termos comuns de sistemas/softwares no texto geral
    sistemas_comuns = ["sap", "totvs", "folha matic", "navision", "elaw", "sapiens", "excel avançado", "gosoft", "legal manager", "foconet", "ecobrança caixa", "itaú banking", "yespay", "smk", "crivo", "receita federal", "mdb", "aciona", "pacote office", "html", "windows", "linux", "microsoft access", "microsoft excel", "microsoft outlook", "microsoft powerpoint", "microsoft word", "open office"]
    
    cv_lower = cv_text.lower()
    for sistema in sistemas_comuns:
        if sistema in cv_lower and sistema.title() not in conhecimentos: # Evita adicionar duplicatas
            conhecimentos.append(sistema.title()) # Adiciona com a primeira letra maiúscula para padronizar

    # Remove duplicatas e retorna como string separada por vírgula
    return ", ".join(sorted(list(set(conhecimentos))))

# NOVAS FUNÇÕES AUXILIARES

def calcular_idade(data_nascimento_str: str) -> int:
    """
    Calcula a idade em anos a partir de uma data de nascimento no formato DD-MM-AAAA.
    Retorna 0 se a data for inválida ou o cálculo não for possível.
    """
    if not data_nascimento_str:
        return 0
    try:
        data_nasc = datetime.strptime(data_nascimento_str, "%d-%m-%Y").date()
        hoje = date.today()
        idade = hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))
        return idade
    except ValueError:
        return 0

def sanitizar_remuneracao(remuneracao_str: str) -> str:
    """
    Limpa e padroniza a string de remuneração.
    Remove caracteres não numéricos exceto a vírgula/ponto decimal.
    Converte vírgula para ponto como separador decimal.
    """
    if not remuneracao_str:
        return ""
    # Remove tudo que não é dígito, vírgula ou ponto
    limpo = re.sub(r'[^\d,.]', '', remuneracao_str)
    # Substitui vírgula por ponto para consistência em float
    limpo = limpo.replace(',', '.')
    
    # Se houver múltiplos pontos, mantém apenas o último (para evitar "1.000.000.00")
    if limpo.count('.') > 1:
        partes = limpo.split('.')
        limpo = "".join(partes[:-1]) + '.' + partes[-1]

    return limpo

def formatar_nivel_profissional(nivel: str) -> str:
    """
    Padroniza o nível profissional para uma lista predefinida.
    """
    nivel_lower = nivel.lower().strip()
    mapeamento = {
        "trainee": "Trainee",
        "junior": "Júnior",
        "júnior": "Júnior",
        "pleno": "Pleno",
        "senior": "Sênior",
        "sênior": "Sênior",
        "especialista": "Especialista",
        "coordenador": "Coordenador",
        "gerente": "Gerente"
    }
    return mapeamento.get(nivel_lower, nivel) # Retorna o original se não encontrar correspondência

def extrair_formacao_academica_do_cv(cv_text: str) -> dict:
    """
    Extrai informações de formação acadêmica (nível, curso, instituição, ano de conclusão)
    do texto do CV, se não estiverem disponíveis nos campos primários do JSON.
    """
    formacao_info = {
        "nivel_academico": "",
        "cursos": "",
        "instituicao_ensino_superior": "",
        "ano_conclusao": ""
    }
    if not cv_text:
        return formacao_info

    # Padrões comuns para seções de formação acadêmica
    # Ex: "Formação acadêmica\n bacharel - ciências contábeis\ncentro universitário ítalo brasileiro\njul/2015 - dez/2018"
    padrao = re.compile(r"formação acadêmica\s*\n(.+?)(?=\n\n|\Z|experiência profissional|histórico profissional|habilidades|resumo profissional)", re.DOTALL | re.IGNORECASE)
    
    match = padrao.search(cv_text)
    if match:
        formacao_bloco = match.group(1).strip()
        lines = [line.strip() for line in formacao_bloco.split('\n') if line.strip()]

        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Nível acadêmico e curso (ex: bacharel - ciências contábeis)
            if "bacharel" in line_lower or "graduação" in line_lower or "ensino superior" in line_lower or "pós-graduação" in line_lower or "mestrado" in line_lower or "doutorado" in line_lower:
                formacao_info["nivel_academico"] = line.replace('', '').strip()
                if '-' in line:
                    parts = line.split('-', 1)
                    if "ensino superior" in parts[0].lower(): # Tratar "ensino superior em administração"
                        formacao_info["cursos"] = parts[0].replace('ensino superior em', '').strip()
                    else:
                        formacao_info["cursos"] = parts[1].strip()
            
            # Instituição de ensino
            # Geralmente a linha seguinte ao curso, ou após um nome de curso
            if "universidade" in line_lower or "faculdade" in line_lower or "centro universitário" in line_lower or "escola" in line_lower:
                 formacao_info["instituicao_ensino_superior"] = line.replace('', '').strip()

            # Ano de conclusão (ex: jul/2015 - dez/2018 ou concluído)
            ano_match = re.search(r'(\d{4})', line)
            if ano_match and "conclusão" in line_lower or "concluído" in line_lower:
                formacao_info["ano_conclusao"] = ano_match.group(1)
            elif re.search(r'\d{4}', line) and ("até" in line_lower or "dez" in line_lower or "jul" in line_lower): # Pega o último ano em um período
                anos_encontrados = re.findall(r'\d{4}', line)
                if anos_encontrados:
                    formacao_info["ano_conclusao"] = anos_encontrados[-1] # Último ano como ano de conclusão
    
    return formacao_info

def sanitizar_link_linkedin(url: str) -> str:
    """
    Garante que um link do LinkedIn comece com 'http://' ou 'https://'.
    """
    if not url:
        return ""
    if not url.startswith("http://") and not url.startswith("https://"):
        return "https://" + url
    return url

# Função principal para preencher os dados do candidato (atualizada)
def preencher_dados_candidato(candidato_data: dict) -> dict:
    """
    Preenche um dicionário de dados do candidato com base na estrutura do prompt,
    utilizando as funções auxiliares para formatação e extração.
    """
    infos_basicas = candidato_data.get("infos_basicas", {})
    informacoes_pessoais = candidato_data.get("informacoes_pessoais", {})
    informacoes_profissionais = candidato_data.get("informacoes_profissionais", {})
    formacao_e_idiomas = candidato_data.get("formacao_e_idiomas", {})
    cv_pt = candidato_data.get("cv_pt", "")

    # Tenta extrair a formação acadêmica do CV se os campos principais estiverem vazios
    formacao_do_cv = extrair_formacao_academica_do_cv(cv_pt)

    # Mapeamento para a estrutura de saída do prompt
    output_data = {
        "infos_basicas": {
            "telefone_recado": formatar_telefone(infos_basicas.get("telefone_recado", "")),
            "telefone": formatar_telefone(infos_basicas.get("telefone", "")),
            "objetivo_profissional": infos_basicas.get("objetivo_profissional", ""),
            "data_criacao": infos_basicas.get("data_criacao", ""),
            "inserido_por": infos_basicas.get("inserido_por", ""),
            "email": infos_basicas.get("email", ""),
            "local": infos_basicas.get("local", ""),
            "sabendo_de_nos_por": infos_basicas.get("sabendo_de_nos_por", ""),
            "data_atualizacao": infos_basicas.get("data_atualizacao", ""),
            "codigo_profissional": infos_basicas.get("codigo_profissional", ""),
            "nome": infos_basicas.get("nome", "")
        },
        "informacoes_pessoais": {
            "data_aceite": informacoes_pessoais.get("data_aceite", "Cadastro via Assistente de Recrutamento"),
            "nome": informacoes_pessoais.get("nome", ""),
            "cpf": informacoes_pessoais.get("cpf", ""),
            "fonte_indicacao": informacoes_pessoais.get("fonte_indicacao", "").replace(":", "").strip(),
            "email": informacoes_pessoais.get("email", ""),
            "email_secundario": informacoes_pessoais.get("email_secundario", ""),
            "data_nascimento": formatar_data_nascimento(informacoes_pessoais.get("data_nascimento", "")),
            "telefone_celular": formatar_telefone(informacoes_pessoais.get("telefone_celular", "")),
            "telefone_recado": formatar_telefone(informacoes_pessoais.get("telefone_recado", "")),
            "sexo": informacoes_pessoais.get("sexo", ""),
            "estado_civil": informacoes_pessoais.get("estado_civil", ""),
            "pcd": informacoes_pessoais.get("pcd", ""),
            "endereco": informacoes_pessoais.get("endereco", ""),
            "skype": informacoes_pessoais.get("skype", ""),
            "url_linkedin": sanitizar_link_linkedin(informacoes_pessoais.get("url_linkedin", "")),
            "facebook": informacoes_pessoais.get("facebook", "")
        },
        "informacoes_profissionais": {
            "titulo_profissional": informacoes_profissionais.get("titulo_profissional", ""),
            "area_atuacao": informacoes_profissionais.get("area_atuacao", ""),
            "conhecimentos_tecnicos": extrair_conhecimentos_tecnicos(cv_pt),
            "certificacoes": informacoes_profissionais.get("certificacoes", ""),
            "outras_certificacoes": informacoes_profissionais.get("outras_certificacoes", ""),
            "remuneracao": sanitizar_remuneracao(informacoes_profissionais.get("remuneracao", "")), # Usando a nova função
            "nivel_profissional": formatar_nivel_profissional(informacoes_profissionais.get("nivel_profissional", "")) # Usando a nova função
        },
        "formacao_e_idiomas": {
            "nivel_academico": formacao_e_idiomas.get("nivel_academico", formacao_do_cv.get("nivel_academico", "")),
            "instituicao_ensino_superior": formacao_e_idiomas.get("instituicao_ensino_superior", formacao_do_cv.get("instituicao_ensino_superior", "")),
            "cursos": formacao_e_idiomas.get("cursos", formacao_do_cv.get("cursos", "")),
            "ano_conclusao": formacao_e_idiomas.get("ano_conclusao", formacao_do_cv.get("ano_conclusao", "")),
            "nivel_ingles": formacao_e_idiomas.get("nivel_ingles", ""),
            "nivel_espanhol": formacao_e_idiomas.get("nivel_espanhol", ""),
            "outro_idioma": formacao_e_idiomas.get("outro_idioma", "-")
        },
        "cargo_atual": candidato_data.get("cargo_atual", {}),
        "cv_pt": extrair_e_formatar_experiencias(cv_pt),
        "cv_en": candidato_data.get("cv_en", "")
    }
    return output_data