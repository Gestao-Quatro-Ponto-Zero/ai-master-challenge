import html.parser
import os
import sys
import unittest

from streamlit.testing.v1 import AppTest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class AppTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file("app.py", default_timeout=30)
        self.app.run()
        self.assertFalse(self.app.exception)

    def navigate(self, page):
        self.app.session_state["os_page"] = page
        self.app.run()
        self.assertFalse(self.app.exception)

    def button(self, label):
        return next(button for button in self.app.button if button.label == label)

    # ------------------------------------------------------------------
    # Home
    # ------------------------------------------------------------------

    def test_home_frames_problem_without_revealing_results(self):
        """Home must sell the problem and reserve results for the simulation."""
        rendered = "\n".join(item.value for item in self.app.markdown)
        self.assertIn("56.306 registros", rendered)
        self.assertIn("O problema de negócio", rendered)
        self.assertIn("O que esta avaliação verifica", rendered)
        self.assertEqual(len(self.app.metric), 0)

    def test_home_primary_cta_starts_case_operation(self):
        """The primary CTA must load the case data in the operational flow."""
        cta = self.button("Iniciar dia com dados do case")
        cta.click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.session_state["os_page"], "Analisar planilhas")
        self.assertTrue(self.app.session_state["use_case_data"])

    def test_home_offers_complete_evaluator_route(self):
        """An evaluator must start without login, uploads or external context."""
        labels = [button.label for button in self.app.button]
        self.assertIn("Iniciar dia com dados do case", labels)
        self.assertIn("Testar uma solicitação", labels)
        self.assertIn("Examinar entregáveis", labels)

        self.button("Iniciar dia com dados do case").click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(
            self.app.session_state["os_page"],
            "Analisar planilhas",
        )
        self.assertTrue(self.app.session_state["use_case_data"])

    def test_home_cards_open_each_operational_area(self):
        """Query-param navigation must route to each operational area."""
        destinations = [
            "Demonstração",
            "Analisar planilhas",
            "Aprendizado",
            "Entregáveis",
            "Ajuda",
        ]
        for destination in destinations:
            with self.subTest(destination=destination):
                app = AppTest.from_file("app.py", default_timeout=30)
                app.query_params["page"] = destination
                app.run()
                self.assertFalse(app.exception)
                self.assertEqual(app.session_state["os_page"], destination)

    def test_horizontal_navigation_replaces_page_dropdown(self):
        """Primary navigation must be visible, linked and free of route selectbox."""
        rendered_html = "\n".join(item.value for item in self.app.markdown)
        self.assertIn("CHALLENGE 002 · REDESIGN DE SUPORTE", rendered_html)
        self.assertIn("<h1>OSS</h1>", rendered_html)
        self.assertIn("Operating System for Support", rendered_html)
        self.assertNotIn("Sistema Operacional do Suporte", rendered_html)
        self.assertIn('class="os-nav"', rendered_html)
        self.assertIn("Navegação principal", rendered_html)
        for label in [
            "Visão geral",
            "Triagem diária",
            "Análise da operação",
            "Aprendizado",
            "Entregáveis",
            "Ajuda",
        ]:
            self.assertIn(label, rendered_html)
        self.assertFalse(
            any(item.label == "Ir para" for item in self.app.selectbox)
        )

    # ------------------------------------------------------------------
    # Demonstração
    # ------------------------------------------------------------------

    def test_matrix_runs_all_cases(self):
        self.navigate("Demonstração")
        self.button("Executar testes do case").click().run()
        self.assertFalse(self.app.exception)
        self.assertTrue(
            any("16/16 casos aprovados" in item.value for item in self.app.success)
        )

    def test_case_dashboard_opens_with_management_metrics(self):
        self.navigate("Demonstração")
        self.button("Abrir painel gerencial do case").click().run()
        self.assertFalse(self.app.exception)
        labels = [metric.label for metric in self.app.metric]
        self.assertIn("Cliente reincidente", labels)
        self.assertIn("Cenário: capacidade líquida", labels)
        self.assertEqual(len(self.app.get("plotly_chart")), 2)

    def test_demo_page_has_single_message_expander(self):
        """Testar uma mensagem must exist as a collapsed expander."""
        self.navigate("Demonstração")
        expander_labels = [e.label for e in self.app.expander]
        self.assertTrue(
            any("Testar uma mensagem" in label for label in expander_labels),
            msg=f"Expected 'Testar uma mensagem' expander; found: {expander_labels}",
        )

    def test_demo_page_has_csv_expander(self):
        """Enviar CSV must exist as a collapsed expander."""
        self.navigate("Demonstração")
        expander_labels = [e.label for e in self.app.expander]
        self.assertTrue(
            any("CSV" in label for label in expander_labels),
            msg=f"Expected CSV expander; found: {expander_labels}",
        )

    def test_customer_complaint_forces_human_care(self):
        """Single-message analysis of a complaint must surface human-care."""
        self.navigate("Demonstração")
        self.app.text_area[0].input(
            "Já falei várias vezes, continuo sem solução e fui cobrado duas vezes."
        )
        self.button("Analisar solicitação").click().run()
        self.assertFalse(self.app.exception)
        metric_values = [metric.value for metric in self.app.metric]
        self.assertIn("Decisão humana", metric_values)
        self.assertIn("Cliente", metric_values)
        self.assertTrue(
            any("Cuidado prioritário" in item.value for item in self.app.error)
        )

    def test_it_hardware_is_only_observed(self):
        self.navigate("Demonstração")
        self.app.radio[0].set_value("Suporte interno de TI")
        self.app.text_area[0].input(
            "The company laptop overheats and shuts down during video calls."
        )
        self.button("Analisar solicitação").click().run()
        self.assertFalse(self.app.exception)
        metric_values = [metric.value for metric in self.app.metric]
        self.assertIn("Equipamento", metric_values)
        self.assertIn("Sugestão em observação", metric_values)

    def test_kill_switch_forces_human_review(self):
        self.app.toggle[0].set_value(True).run()
        self.navigate("Demonstração")
        self.app.radio[0].set_value("Suporte interno de TI")
        self.app.text_area[0].input(
            "The company laptop overheats and shuts down during video calls."
        )
        self.button("Analisar solicitação").click().run()
        self.assertFalse(self.app.exception)
        metric_values = [metric.value for metric in self.app.metric]
        self.assertIn("Decisão humana", metric_values)

    def test_known_purchase_error_activates_memory(self):
        self.navigate("Demonstração")
        demo = next(
            item for item in self.app.selectbox
            if item.label == "Caso de demonstração"
        )
        demo.select("Erro conhecido de compra").run()
        self.button("Analisar solicitação").click().run()
        self.assertFalse(self.app.exception)
        metric_values = [metric.value for metric in self.app.metric]
        self.assertIn("Decisão humana", metric_values)
        markdown = "\n".join(item.value for item in self.app.markdown)
        self.assertIn("Aprendizado anterior acionado", markdown)

    # ------------------------------------------------------------------
    # Outras páginas
    # ------------------------------------------------------------------

    def test_learning_page_is_seeded_and_explains_limits(self):
        self.navigate("Aprendizado")
        self.assertGreaterEqual(len(self.app.dataframe), 2)
        operational = self.app.dataframe[0].value
        corrections = self.app.dataframe[1].value
        self.assertEqual(len(operational), 6)
        self.assertGreaterEqual(len(corrections), 1)
        markdown = "\n".join(item.value for item in self.app.markdown)
        self.assertIn("Por que não retropropagação agora?", markdown)
        self.assertIn("Por que não RAG agora?", markdown)

    def test_deliverables_are_inside_the_os_and_guided(self):
        """Entregáveis must show criteria, guided files and first-person notes."""
        self.navigate("Entregáveis")
        downloads = self.app.get("download_button")
        self.assertEqual(
            sum(button.label == "Baixar .md" for button in downloads),
            0,
            msg="Markdown deliverables must open inside the OS.",
        )
        read_buttons = [
            button for button in self.app.button if button.label == "Ler agora"
        ]
        self.assertEqual(len(read_buttons), 11)
        self.assertTrue(
            any(button.label == "Baixar matriz de testes" for button in downloads),
            msg="Expected 'Baixar matriz de testes' button",
        )

        # Check expander labels
        expander_labels = [e.label for e in self.app.expander]
        self.assertIn("1. Decisão", expander_labels)
        self.assertIn("2. Evidência", expander_labels)
        self.assertIn("3. Limites", expander_labels)
        self.assertIn("4. Execução", expander_labels)
        self.assertIn("Arquivos de submissão", expander_labels)
        self.assertIn(
            "Mapa rápido: onde entra IA e onde ela para",
            expander_labels,
        )

        # Check top summary criteria & Pedro notes across caption and markdown elements
        all_text = "\n".join(
            [item.value for item in self.app.caption]
            + [item.value for item in self.app.markdown]
        )
        self.assertIn("Números do Dataset 1", all_text)
        self.assertIn("Uso material dos dois datasets", all_text)
        self.assertIn("Protótipo funcional", all_text)
        self.assertIn("Process log", all_text)

        # Check first-person editorial notes
        self.assertIn("Minha nota: comece aqui", all_text)
        self.assertIn("Minha nota: confira a prova", all_text)
        self.assertIn("Minha nota: aqui eu decidi não automatizar", all_text)
        self.assertNotIn("vivência de Pedro", all_text)
        self.assertNotIn("Nota do Pedro", all_text)

        frontier = next(
            dataframe.value
            for dataframe in self.app.dataframe
            if "Ponto do fluxo" in dataframe.value.columns
        )
        self.assertEqual(len(frontier), 8)
        self.assertIn("IA sugere", frontier["Responsável"].tolist())
        self.assertIn("Humano", frontier["Responsável"].tolist())
        self.assertIn("Código", frontier["Responsável"].tolist())

        read_buttons[0].click().run()
        self.assertFalse(self.app.exception)
        dialog_text = "\n".join(item.value for item in self.app.markdown)
        self.assertIn("Parecer 80/20 da operação", dialog_text)
        self.assertIn("Quatro indicadores comprovados", dialog_text)

    def test_universal_analysis_starts_with_two_uploads(self):
        self.navigate("Analisar planilhas")
        self.assertIn(
            "Iniciar dia com dados do case",
            [button.label for button in self.app.button],
        )
        self.assertEqual(len(self.app.file_uploader), 2)
        self.assertEqual(
            [uploader.label for uploader in self.app.file_uploader],
            ["Planilha 1", "Planilha 2"],
        )

    def test_universal_analysis_loads_case_samples_without_upload(self):
        self.navigate("Analisar planilhas")
        case_button = next(
            button
            for button in self.app.button
            if button.label == "Iniciar dia com dados do case"
        )
        case_button.click()
        self.app.run()
        self.assertFalse(self.app.exception)
        self.assertTrue(
            any(
                "Dados do case carregados" in item.value
                for item in self.app.success
            )
        )
        rendered_text = "\n".join(
            [item.value for item in self.app.markdown]
            + [item.value for item in self.app.caption]
        )
        self.assertIn("Dataset 1: amostra do atendimento", rendered_text)
        self.assertIn("Dataset 2: amostra de suporte de TI", rendered_text)
        metric_labels = [metric.label for metric in self.app.metric]
        self.assertIn("Bases carregadas", metric_labels)
        self.assertIn("Linhas disponíveis", metric_labels)
        self.assertIn("Linhas a analisar", metric_labels)
        self.assertIn("Colunas aceitas", metric_labels)
        self.assertIn(
            "Aprovar estrutura e analisar",
            [button.label for button in self.app.button],
        )

        limit = next(
            item
            for item in self.app.number_input
            if item.label == "Máximo de linhas por base nesta análise"
        )
        limit.set_value(4000).run()
        values = {
            metric.label: metric.value
            for metric in self.app.metric
        }
        self.assertEqual(values["Linhas a analisar"], "8.000")
        self.assertTrue(
            any(
                "até 4.000 linha(s) por base" in item.value
                and "8.000 de 10.000" in item.value
                and "2.000 linha(s) ficarão fora" in item.value
                for item in self.app.info
            )
        )

    def test_universal_opinion_turns_analysis_into_action(self):
        self.navigate("Analisar planilhas")
        self.button("Iniciar dia com dados do case").click().run()
        self.button("Aprovar estrutura e analisar").click().run()
        self.assertFalse(self.app.exception)

        self.button("Ver decisão e fila prioritária").click().run()
        self.assertFalse(self.app.exception)
        rendered = "\n".join(item.value for item in self.app.markdown)
        written = "\n".join(str(item.value) for item in self.app.info)
        self.assertIn("Veredito", rendered)
        self.assertIn("Operação apta para piloto assistido", rendered)
        self.assertIn("Limitação do ROI", rendered)
        self.assertIn("Agora:", written)

        labels = [button.label for button in self.app.button]
        self.assertIn("Abrir fila prioritária", labels)
        self.assertIn("Ver evidências", labels)
        self.assertTrue(
            any(
                button.label == "Baixar parecer"
                for button in self.app.get("download_button")
            )
        )

        self.button("Abrir fila prioritária").click().run()
        self.assertFalse(self.app.exception)
        rendered = "\n".join(item.value for item in self.app.markdown)
        self.assertIn("Fila prioritária", rendered)

        self.button("Ver evidências").click().run()
        self.assertFalse(self.app.exception)
        rendered = "\n".join(item.value for item in self.app.markdown)
        self.assertIn("Evidências da análise", rendered)


if __name__ == "__main__":
    unittest.main()
