import tkinter as tk
import math
import json

class GraphDrawer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.image = tk.PhotoImage(width=width, height=height)
    
    # Function to plot a pixel
    def plot_pixel(self, x, y, color):
        self.image.put(color, (x, y))
    
    # Bresenham's Line Algorithm to draw a straight line
    def draw_line(self, x1, y1, x2, y2, color):
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            self.plot_pixel(x1, y1, color)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy
    
    # Midpoint Circle Algorithm to draw an arc
    def draw_arc(self, xc, yc, r, start_angle, end_angle, color):
        x = 0
        y = r
        d = 1 - r
        self.plot_arc_points(xc, yc, x, y, start_angle, end_angle, color)
        
        while x < y:
            x += 1
            if d < 0:
                d = d + 2 * x + 1
            else:
                y -= 1
                d = d + 2 * (x - y) + 1
            self.plot_arc_points(xc, yc, x, y, start_angle, end_angle, color)
    
    # Plot arc points based on the angle range
    def plot_arc_points(self, xc, yc, x, y, start_angle, end_angle, color):
        points = [
            (xc + x, yc + y), (xc - x, yc + y),
            (xc + x, yc - y), (xc - x, yc - y),
            (xc + y, yc + x), (xc - y, yc + x),
            (xc + y, yc - x), (xc - y, yc - x)
        ]
        
        for (px, py) in points:
            angle = math.degrees(math.atan2(py - yc, px - xc))
            if start_angle <= angle <= end_angle or start_angle <= angle + 360 <= end_angle:
                self.plot_pixel(px, py, color)
    
    # Function to draw nodes as small circles
    def draw_node(self, x, y, r, color):
        self.draw_arc(x, y, r, 0, 360, color)  # A full circle is just an arc from 0 to 360 degrees
    
    # Function to find a point on the circumference of a node based on the angle
    def point_on_circumference(self, xc, yc, r, angle):
        radians = math.radians(angle)
        x = xc + r * math.cos(radians)
        y = yc + r * math.sin(radians)
        return int(x), int(y)
    
    # Draw an edge from the circumference of one node to the circumference of another
    def draw_edge(self, x1, y1, x2, y2, r1, r2, color):
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        source_x, source_y = self.point_on_circumference(x1, y1, r1, angle)
        dest_x, dest_y = self.point_on_circumference(x2, y2, r2, angle + 180)
        self.draw_line(source_x, source_y, dest_x, dest_y, color)

    # Draw an arc between two points on the circumference of nodes
    def draw_arc_edge(self, x1, y1, x2, y2, r1, r2, color):
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        source_x, source_y = self.point_on_circumference(x1, y1, r1, angle)
        dest_x, dest_y = self.point_on_circumference(x2, y2, r2, angle + 180)
        
        arc_center_x = (x1 + x2) // 2
        arc_center_y = (y1 + y2) // 2 + 100  # Raise arc center for visibility
        arc_radius = math.dist((arc_center_x, arc_center_y), (source_x, source_y))
        
        start_angle = math.degrees(math.atan2(source_y - arc_center_y, source_x - arc_center_x))
        end_angle = math.degrees(math.atan2(dest_y - arc_center_y, dest_x - arc_center_x))
        self.draw_arc(arc_center_x, arc_center_y, int(arc_radius), start_angle, end_angle, color)

    # Load and draw graph from JSON structure
    def load_graph(self, graph_data):
        node_radius = 30
        node_count = len(graph_data["nodes"])
        node_positions = []
        spacing = (self.width - (2 * node_radius)) // (node_count + 1)  # Calculate spacing for nodes
        
        for i in range(node_count):
            x = (i + 1) * spacing + node_radius
            # Adjust y-coordinates for Node 1 to be higher
            y = self.height // 2 - (20 if i == 0 else 0)  # Node 1 is raised by 20 pixels
            node_positions.append((x, y))
        
        for (node, (x, y)) in zip(graph_data["nodes"], node_positions):
            self.draw_node(x, y, node_radius, "black")

        for edge in graph_data["edges"]:
            from_node = edge["from"]
            to_node = edge["to"]
            from_position = node_positions[from_node - 1]
            to_position = node_positions[to_node - 1]
            self.draw_edge(from_position[0], from_position[1], to_position[0], to_position[1], node_radius, node_radius, "black")

            if from_node == 1 and to_node == 3:
                self.draw_arc_edge(from_position[0], from_position[1], to_position[0], to_position[1], node_radius, node_radius, "black")

            if from_node == 1 and to_node == 4:
                self.draw_arc_edge(from_position[0], from_position[1], to_position[0], to_position[1], node_radius, node_radius, "black")

    def display(self, root):
        label = tk.Label(root, image=self.image)
        label.pack()

root = tk.Tk()
drawer = GraphDrawer(600, 400)

graph_json = '''{
    "nodes": [
        {"id": 1, "label": "Node 1"},
        {"id": 2, "label": "Node 2"},
        {"id": 3, "label": "Node 3"},
        {"id": 4, "label": "Node 4"}
    ],
    "edges": [
        {"from": 1, "to": 2},
        {"from": 2, "to": 3},
        {"from": 3, "to": 4},
        {"from": 1, "to": 3},
        {"from": 1, "to": 4}
    ]
}'''

graph_data = json.loads(graph_json)
drawer.load_graph(graph_data)
drawer.display(root)
root.mainloop()
