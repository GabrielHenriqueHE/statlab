"""Formatação pt-BR e entrada de dados (conversão, faltantes, pareamento, validações)."""

import numpy as np
import pytest

from statlab.core.dados import ErroDeDados, amostra, exigir_variacao, numero, pares, parse_lista
from statlab.core.formatacao import lista, num, p_numero, p_valor, pct


class TestFormatacao:
    def test_num_padrao_brasileiro(self):
        assert num(1452.781) == "1.452,78"
        assert num(-0.5) == "-0,50"
        assert num(2.0, 0) == "2"
        assert num(1234567.891, 1) == "1.234.567,9"

    def test_num_nao_finito_nao_vaza_nan(self):
        assert num(float("nan")) == "—"
        assert num(float("inf")) == "—"

    def test_p_valor_regra_da_apostila(self):
        assert p_valor(0.0004) == "< 0,001"
        assert p_valor(0.047) == "= 0,047"
        assert p_valor(0.0519) == "= 0,052"
        assert p_numero(0.0004) == "< 0,001"
        assert p_numero(None) == "—"

    def test_lista_inteiros_sem_casas(self):
        assert lista([15, 40.0, 31.5]) == "15; 40; 31,5"

    def test_pct(self):
        assert pct(92.1) == "92,1%"


class TestNumero:
    @pytest.mark.parametrize(
        "entrada, esperado",
        [
            (3, 3.0),
            (2.5, 2.5),
            ("1,5", 1.5),
            ("1.100", 1100.0),  # ponto de milhar pt-BR
            ("1.234,5", 1234.5),
            ("-0,35", -0.35),
            ("0.5", 0.5),  # ponto decimal quando não parece milhar
            ("  7 ", 7.0),
            ("", None),
            (None, None),
            (float("nan"), None),
        ],
    )
    def test_conversao(self, entrada, esperado):
        assert numero(entrada) == esperado

    @pytest.mark.parametrize("ruim", ["abc", True, float("inf")])
    def test_rejeita_nao_numerico(self, ruim):
        with pytest.raises(ErroDeDados):
            numero(ruim)


class TestAmostraEPares:
    def test_amostra_conta_faltantes(self):
        v, falt = amostra([1, None, "2,5", "", 4], "grupo")
        assert list(v) == [1.0, 2.5, 4.0]
        assert falt == 2

    def test_amostra_mensagem_traz_o_nome(self):
        with pytest.raises(ErroDeDados, match="Grupo X"):
            amostra([1, "x"], "Grupo X")

    def test_pares_descarta_incompletos_e_colunas_desiguais(self):
        x, y, desc = pares([1, 2, 3, 4, 5, 6], [10, None, 30, 40])  # y tem 4, x tem 6
        assert list(x) == [1.0, 3.0, 4.0]
        assert list(y) == [10.0, 30.0, 40.0]
        assert desc == 3  # par 2 (y faltante), e pares 5 e 6 (y ausente)

    def test_pares_exige_as_duas_colunas(self):
        with pytest.raises(ErroDeDados):
            pares(None, [1, 2])


class TestValidacoes:
    def test_exigir_variacao_coluna_constante(self):
        with pytest.raises(ErroDeDados, match="todos os valores são iguais"):
            exigir_variacao(np.array([5.0, 5.0, 5.0]), "x")

    def test_exigir_variacao_aceita_valores_distintos(self):
        exigir_variacao(np.array([5.0, 6.0]), "x")  # não levanta


class TestParseLista:
    def test_separadores_mistos(self):
        assert parse_lista("15; 40\n31\t25 48") == [15.0, 40.0, 31.0, 25.0, 48.0]

    def test_ignora_separadores_repetidos_e_vazios(self):
        assert parse_lista(" 1;; 2 ;\n") == [1.0, 2.0]

    def test_pt_br_dentro_da_lista(self):
        assert parse_lista("1.100; 2,5") == [1100.0, 2.5]

    def test_erro_aponta_o_item(self):
        with pytest.raises(ErroDeDados, match="abc"):
            parse_lista("1; abc; 3")
