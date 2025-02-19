import pygame
import sys
import re
import json

def approve_changes(left_file, right_text, changes):
    def break_line(text, font, max_width):
        """
        Quebra uma linha de texto em várias linhas que cabem dentro de max_width.
        """
        words = text.split(' ')
        lines = []
        current_line = words[0]

        for word in words[1:]:
            width, _ = font.size(current_line + ' ' + word)
            if width <= max_width:
                current_line += ' ' + word
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)

        return lines

    def render_markdown_text(surface, text, fonts, pos, color, max_width=None, 
                             highlight_color=(40, 45, 50), code_bg_color=(60, 63, 65)):
        """
        Renderiza um texto em Markdown utilizando Pygame.

        Adiciona tratamento para blocos de código delimitados por três crases.
        Se uma linha iniciar com "%%RED%%", ela terá fundo vermelho.
        """
        x, y = pos
        lines = text.splitlines()
        in_code_block = False
        code_lines = []
        
        for line in lines:
            # Se a linha indicar início ou fim de bloco de código
            if line.strip().startswith("```"):
                if not in_code_block:
                    in_code_block = True
                    code_lines = []
                else:
                    # Finaliza o bloco e renderiza-o
                    for code_line in code_lines:
                        wrapped = break_line(code_line, fonts["normal"], max_width) if max_width else [code_line]
                        for part in wrapped:
                            render_surf = fonts["normal"].render(part, True, color)
                            text_rect = render_surf.get_rect(topleft=(x, y))
                            pygame.draw.rect(surface, code_bg_color, text_rect)
                            surface.blit(render_surf, (x, y))
                            y += render_surf.get_height()
                    y += fonts["normal"].get_height() // 2
                    in_code_block = False
                continue
            
            if in_code_block:
                code_lines.append(line)
                continue
            
            # Verifica se a linha deve ser destacada com fundo vermelho
            red_highlight = False
            if line.startswith("%%RED%%"):
                red_highlight = True
                line = line[len("%%RED%%"):]  # remove o marcador

            # Verifica se a linha deve ser destacada com fundo verde
            green_highlight = False
            if line.startswith("%%GREEN%%"):
                green_highlight = True
                line = line[len("%%GREEN%%"):]  # remove o marcador
            
            if not line.strip():
                y += fonts["normal"].get_height()
                continue
            
            # Define o estilo da linha para cabeçalhos e listas
            if line.startswith("#"):
                while line.startswith("#"):
                    line = line[1:]
                line = line.strip()
                current_font = fonts.get("header", fonts["normal"])
            elif line.startswith("-"):
                line = "• " + line[1:].strip()
                current_font = fonts["normal"]
            else:
                current_font = fonts["normal"]
            
            # Se a linha for para destaque vermelho, ignora o processamento inline de Markdown
            # e renderiza a linha inteira com fundo vermelho
            if red_highlight:
                wrapped = break_line(line, current_font, max_width) if max_width else [line]
                for part in wrapped:
                    render_surf = current_font.render(part, True, color)
                    text_rect = render_surf.get_rect(topleft=(x, y))
                    pygame.draw.rect(surface, (100, 0, 0), text_rect)  # fundo vermelho
                    surface.blit(render_surf, (x, y))
                    y += current_font.get_height()
                continue

            # Se a linha for para destaque verde, ignora o processamento inline de Markdown
            # e renderiza a linha inteira com fundo verde
            if green_highlight:
                wrapped = break_line(line, current_font, max_width) if max_width else [line]
                for part in wrapped:
                    render_surf = current_font.render(part, True, color)
                    text_rect = render_surf.get_rect(topleft=(x, y))
                    pygame.draw.rect(surface, (0, 100, 0), text_rect)  # fundo verde
                    surface.blit(render_surf, (x, y))
                    y += current_font.get_height()
                continue
            
            # Caso não seja linha destacada, processa normalmente o Markdown inline
            rendered_lines = break_line(line, current_font, max_width) if max_width else [line]
            for part in rendered_lines:
                segments = re.split(r'(\*\*.*?\*\*|`.*?`)', part)
                current_x = x
                for segment in segments:
                    if segment.startswith("**") and segment.endswith("**"):
                        seg_text = segment[2:-2]
                        old_bold = current_font.get_bold()
                        current_font.set_bold(True)
                        render_surf = current_font.render(seg_text, True, color)
                        current_font.set_bold(old_bold)
                    elif segment.startswith("`") and segment.endswith("`"):
                        seg_text = segment[1:-1]
                        render_surf = current_font.render(seg_text, True, color)
                        text_rect = render_surf.get_rect(topleft=(current_x, y))
                        pygame.draw.rect(surface, highlight_color, text_rect)
                    else:
                        render_surf = current_font.render(segment, True, color)
                    surface.blit(render_surf, (current_x, y))
                    current_x += render_surf.get_width()
                y += current_font.get_height()

    def calculate_markdown_height(text, fonts, max_width=None, 
                                highlight_color=(40, 45, 50), code_bg_color=(60, 63, 65)):
        """
        Calcula a altura necessária para renderizar o texto Markdown.
        """
        y = 0
        lines = text.splitlines()
        in_code_block = False
        code_lines = []
        
        for line in lines:
            if line.strip().startswith("```"):
                if not in_code_block:
                    in_code_block = True
                    code_lines = []
                else:
                    # Processa bloco de código
                    for code_line in code_lines:
                        wrapped = break_line(code_line, fonts["normal"], max_width) if max_width else [code_line]
                        for part in wrapped:
                            y += fonts["normal"].get_height()
                    y += fonts["normal"].get_height() // 2
                    in_code_block = False
                continue
            
            if in_code_block:
                code_lines.append(line)
                continue
            
            line = line.strip()
            if not line:
                y += fonts["normal"].get_height()
                continue
            
            if line.startswith("#"):
                while line.startswith("#"):
                    line = line[1:]
                line = line.strip()
                current_font = fonts.get("header", fonts["normal"])
            elif line.startswith("-"):
                line = "• " + line[1:].strip()
                current_font = fonts["normal"]
            else:
                current_font = fonts["normal"]
            
            rendered_lines = break_line(line, current_font, max_width) if max_width else [line]
            y += len(rendered_lines) * current_font.get_height()
        
        return y
    
    def highlight_left_text(text, changes):
        """
        Destaca com vermelho as linhas do texto que estão nos intervalos definidos em changes.
        
        Essa função insere o marcador "%%RED%%" no início de cada linha que deverá ser destacada.
        Após aplicar essa função, você pode modificar a renderização (por exemplo, em render_markdown_text)
        para desenhar essas linhas com fundo vermelho.
        
        Parâmetros:
        - text: string com o conteúdo original (left_text);
        - changes: dicionário com a chave "alteracoes" contendo intervalos de linhas (1-indexado) com "inicio" e "fim".
        
        Retorna:
        - Uma nova string com os marcadores inseridos nas linhas correspondentes.
        """
        lines = text.splitlines()
        for alteration in changes.get("alteracoes", []):
            inicio = alteration.get("inicio", 1)
            fim = alteration.get("fim", inicio)
            # Ajusta para índice 0-baseado e evita extrapolar o tamanho da lista
            for i in range(inicio - 1, min(fim, len(lines))):
                # Insere o marcador caso ainda não esteja presente
                if not lines[i].startswith("%%RED%%"):
                    lines[i] = "%%RED%%" + lines[i]
        return "\n".join(lines)
    
    def highlight_right_text(text, changes):
        lines = text.splitlines()
        for alteration in changes.get("alteracoes", []):
            novo_conteudos = alteration.get("novo_conteudo", "")
            novo_conteudos = novo_conteudos.split("\n")
            for i in range(len(lines)):
                for conteudo in novo_conteudos:
                    if lines[i].strip() == conteudo.strip():
                        if not lines[i].startswith("%%GREEN%%"):
                            lines[i] = "%%GREEN%%" + lines[i]
        return "\n".join(lines)

    # Inicialização do Pygame
    pygame.init()
    screen_width = 1400
    screen_height = 900
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Approve Changes")
    
    icon = pygame.image.load('git-icon.png')
    pygame.display.set_icon(icon)
    
    # Cores e fontes
    background_color = (13, 17, 23)
    panel_color = (17, 21, 27)  
    border_color = (48, 54, 61)  
    header_bg_color = (22, 27, 34)
    text_color = (201, 209, 217)
    
    font = pygame.font.SysFont('Calibri', 18)
    font_header = pygame.font.SysFont('Calibri', 20)
    fonts = {"header": font_header, "normal": font}
    
    # Dimensões dos painéis
    panel_width = (screen_width // 2) - 60  
    panel_height = screen_height - 100      
    panel_y = 40                            
    
    # Painéis
    panel_left_x = 30
    panel_left_rect = pygame.Rect(panel_left_x, panel_y, panel_width, panel_height)
    
    panel_right_x = screen_width - panel_width - 30
    panel_right_rect = pygame.Rect(panel_right_x, panel_y, panel_width, panel_height)
    
    # Cabeçalhos
    header_height = 40
    header_left_rect = pygame.Rect(panel_left_x, panel_y, panel_width, header_height)
    header_right_rect = pygame.Rect(panel_right_x, panel_y, panel_width, header_height)
    
    title_left = "Current Documentation:"
    title_right = "New Documentation:"
    
    clock = pygame.time.Clock()
    running = True
    resultado = None  # Variável que armazenará o resultado: True ou False
    
    # Variável de scroll para o conteúdo do painel
    left_scroll_y = 0
    right_scroll_y = 0

    # Altura disponível para renderização do conteúdo (dentro do painel, descontando cabeçalho e margens)
    left_viewport_height = panel_height - header_height - 20
    right_viewport_height = panel_height - header_height - 20

    # Ajusta os textos
    with open(left_file, 'r', encoding='utf-8') as f:
        left_text = f.read()
    right_text = "\n".join(right_text)

    # Renderize todo o conteúdo do painel esquerdo em uma superfície maior
    left_content_height = calculate_markdown_height(left_text, fonts, max_width=panel_width - 20)
    right_content_height = calculate_markdown_height(right_text, fonts, max_width=panel_width - 20)
    left_text_surface = pygame.Surface((panel_width - 20, 740))
    right_text_surface = pygame.Surface((panel_width - 20, 740))
    
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                resultado = None
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in (4, 5):
                    mouse_pos = pygame.mouse.get_pos()
                    # Se o mouse estiver sobre o painel esquerdo
                    if panel_left_rect.collidepoint(mouse_pos):
                        if event.button == 4:  # Scroll para cima
                            left_scroll_y = min(left_scroll_y + 20, 0)
                        elif event.button == 5:  # Scroll para baixo
                            left_limit = left_viewport_height - left_content_height
                            left_scroll_y = max(left_scroll_y - 20, left_limit)
                    # Se o mouse estiver sobre o painel direito
                    elif panel_right_rect.collidepoint(mouse_pos):
                        if event.button == 4:  # Scroll para cima
                            right_scroll_y = min(right_scroll_y + 20, 0)
                        elif event.button == 5:  # Scroll para baixo
                            right_limit = right_viewport_height - right_content_height
                            right_scroll_y = max(right_scroll_y - 20, right_limit)
                
                # Verifica cliques nos botões Aprovar/Recusar
                mouse_pos = pygame.mouse.get_pos()
                if aprovar_rect.collidepoint(mouse_pos):
                    resultado = True
                    running = False
                elif recusar_rect.collidepoint(mouse_pos):
                    resultado = False
                    running = False
        
        screen.fill(background_color)
        
        # Desenhar painéis
        pygame.draw.rect(screen, panel_color, panel_left_rect, border_radius=15)
        pygame.draw.rect(screen, panel_color, panel_right_rect, border_radius=15)
        pygame.draw.rect(screen, border_color, panel_left_rect, 1, border_radius=15)
        pygame.draw.rect(screen, border_color, panel_right_rect, 1, border_radius=15)
        
        # Desenhar cabeçalhos com bordas superiores arredondadas
        pygame.draw.rect(screen, header_bg_color, header_left_rect, border_top_left_radius=15, border_top_right_radius=15)
        pygame.draw.rect(screen, header_bg_color, header_right_rect, border_top_left_radius=15, border_top_right_radius=15)
        pygame.draw.rect(screen, border_color, header_left_rect, 1, border_top_left_radius=15, border_top_right_radius=15)
        pygame.draw.rect(screen, border_color, header_right_rect, 1, border_top_left_radius=15, border_top_right_radius=15)
        
        # Renderizar textos do cabeçalho
        title_left_surf = font_header.render(title_left, True, text_color)
        title_right_surf = font_header.render(title_right, True, text_color)
        padding = 18
        title_left_rect = title_left_surf.get_rect(midleft=(header_left_rect.left + padding, header_left_rect.centery))
        title_right_rect = title_right_surf.get_rect(midleft=(header_right_rect.left + padding, header_right_rect.centery))
        screen.blit(title_left_surf, title_left_rect)
        screen.blit(title_right_surf, title_right_rect)

        # Converte changes para json
        if isinstance(changes, str):
            changes = json.loads(changes)

        # Destaca as linhas com as alterações
        left_text = highlight_left_text(left_text, changes)
        right_text = highlight_right_text(right_text, changes)
        
        # Renderiza o conteúdo do painel esquerdo na superfície maior
        left_text_surface.fill(panel_color)  # limpa a superfície com a cor do painel
        right_text_surface.fill(panel_color)  # limpa a superfície com a cor do painel
        render_markdown_text(left_text_surface, left_text, fonts, (0, left_scroll_y), text_color, max_width=panel_width - 20)
        render_markdown_text(right_text_surface, right_text, fonts, (0, right_scroll_y), text_color, max_width=panel_width - 20)
        
        # Blita apenas a parte visível da left_text_surface para o painel esquerdo
        viewport_rect = pygame.Rect(0, 0, panel_width - 20, left_viewport_height)
        screen.blit(left_text_surface, (panel_left_x + 10, panel_y + header_height + 10), area=viewport_rect)

        # Blita apenas a parte visível da right_text_surface para o painel direito
        viewport_rect = pygame.Rect(0, 0, panel_width - 20, right_viewport_height)
        screen.blit(right_text_surface, (panel_right_x + 10, panel_y + header_height + 10), area=viewport_rect)
        
        # Botões Aprovar e Recusar no canto inferior direito
        btn_width = 100
        btn_height = 30
        margin = 20
        aprovar_rect = pygame.Rect(screen_width - margin - (btn_width * 2) - 10, screen_height - margin - btn_height, btn_width, btn_height)
        recusar_rect = pygame.Rect(screen_width - margin - btn_width, screen_height - margin - btn_height, btn_width, btn_height)
        
        pygame.draw.rect(screen, (0, 128, 0), aprovar_rect, border_radius=5)  # Botão Aprovar (verde)
        pygame.draw.rect(screen, (128, 0, 0), recusar_rect, border_radius=5)   # Botão Recusar (vermelho)
        
        aprovar_text = font_header.render("Accept", True, (255, 255, 255))
        recusar_text = font_header.render("Discard", True, (255, 255, 255))
        
        aprovar_text_rect = aprovar_text.get_rect(center=aprovar_rect.center)
        recusar_text_rect = recusar_text.get_rect(center=recusar_rect.center)
        
        screen.blit(aprovar_text, aprovar_text_rect)
        screen.blit(recusar_text, recusar_text_rect)
        
        pygame.display.flip()
    
    pygame.quit()
    return resultado
