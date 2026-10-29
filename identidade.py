"""Identificação apenas para a DEMONSTRAÇÃO.

CPF matematicamente válido não comprova identidade. Nunca use nome+CPF como
autenticação suficiente para dados reais, motoristas ou operações comerciais.
Não cole dados reais no site público de testes.
"""
import hashlib
import hmac
import os
import re
import unicodedata

# Chave pública, fictícia e insegura por desenho: SOMENTE protótipo.
_CHAVE_DEMO = os.environ.get("ROTAS_CPF_DEMO_KEY", "central-rotas-demo-nao-usar-em-producao")


def limpar_cpf(texto):
    bruto = str(texto).strip()
    if not re.fullmatch(r"[0-9.\- ]{11,18}", bruto):
        return None
    numero = re.sub(r"\D", "", bruto)
    return numero if len(numero) == 11 else None


def cpf_valido(texto):
    numero = limpar_cpf(texto)
    if not numero or len(set(numero)) == 1:
        return False

    def digito(parcial):
        fator = len(parcial) + 1
        soma = sum(int(n) * (fator - i) for i, n in enumerate(parcial))
        resultado = (soma * 10) % 11
        return 0 if resultado == 10 else resultado

    return (digito(numero[:9]) == int(numero[9])
            and digito(numero[:10]) == int(numero[10]))


def assinatura_cpf(texto):
    """Digest irreversível apenas para evitar CPF explícito no SQLite demo."""
    numero = limpar_cpf(texto)
    if not numero or not cpf_valido(numero):
        raise ValueError("CPF fictício inválido")
    return hmac.new(_CHAVE_DEMO.encode("utf-8"),
                    numero.encode("ascii"), hashlib.sha256).hexdigest()


def normalizar_nome(texto):
    compacto = " ".join(str(texto).split())
    sem_acentos = unicodedata.normalize("NFKD", compacto)
    sem_acentos = "".join(c for c in sem_acentos if not unicodedata.combining(c))
    return sem_acentos.casefold()


def nome_valido(texto):
    nome = " ".join(str(texto).split())
    return (2 <= len(nome) <= 80
            and any(caractere.isalpha() for caractere in nome)
            and all(c.isalpha() or c in " -'’" for c in nome))
