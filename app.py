import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.lib.utils import ImageReader
import os

class ImageToPdfConverter(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Image to PDF Converter")
        self.geometry("800x600")

        # --- Data Storage ---
        self.image_paths = []
        self.preview_image = None # To prevent garbage collection

        # --- UI Configuration ---
        self.configure(bg="#f0f0f0")
        style = ttk.Style(self)
        style.configure("TButton", padding=6, relief="flat", background="#e1e1e1")
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0")

        # --- Main Layout Frames ---
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid layout
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1, minsize=200)
        main_frame.grid_columnconfigure(1, weight=3)

        # --- Top Controls Frame ---
        top_controls_frame = ttk.Frame(main_frame)
        top_controls_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        self.browse_button = ttk.Button(top_controls_frame, text="Browse for Images", command=self.browse_images)
        self.browse_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.convert_button = ttk.Button(top_controls_frame, text="Convert to PDF", command=self.convert_to_pdf)
        self.convert_button.pack(side=tk.LEFT)
        
        # --- PDF Options ---
        orientation_label = ttk.Label(top_controls_frame, text="Orientation:")
        orientation_label.pack(side=tk.LEFT, padx=(20, 5))
        
        self.orientation_var = tk.StringVar(value="Portrait")
        self.orientation_menu = ttk.Combobox(top_controls_frame, textvariable=self.orientation_var, values=["Portrait", "Landscape"], state="readonly", width=10)
        self.orientation_menu.pack(side=tk.LEFT)
        self.orientation_menu.bind("<<ComboboxSelected>>", self.on_orientation_change)

        # --- Left Frame for Image List ---
        left_frame = ttk.Frame(main_frame, padding="5")
        left_frame.grid(row=1, column=0, sticky="nswe", padx=(0, 10))
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        self.image_listbox = tk.Listbox(left_frame, selectmode=tk.SINGLE)
        self.image_listbox.grid(row=0, column=0, columnspan=3, sticky="nswe")
        self.image_listbox.bind("<<ListboxSelect>>", self.show_preview)
        
        # Listbox controls
        self.move_up_button = ttk.Button(left_frame, text="▲ Up", command=self.move_up)
        self.move_up_button.grid(row=1, column=0, sticky="ew", pady=(5,0))

        self.move_down_button = ttk.Button(left_frame, text="▼ Down", command=self.move_down)
        self.move_down_button.grid(row=1, column=1, sticky="ew", pady=(5,0))

        self.remove_button = ttk.Button(left_frame, text="Remove", command=self.remove_image)
        self.remove_button.grid(row=1, column=2, sticky="ew", pady=(5,0))

        # --- Right Frame for Image Preview ---
        right_frame = ttk.Frame(main_frame, padding="5")
        right_frame.grid(row=1, column=1, sticky="nswe")
        
        # Add orientation info label
        self.orientation_info = ttk.Label(right_frame, text="Preview: Portrait A4", font=("Arial", 10, "bold"))
        self.orientation_info.pack(pady=(0, 5))
        
        self.preview_label = ttk.Label(right_frame, text="Image Preview will be shown here", anchor="center", background="#cccccc")
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        # --- Status Bar ---
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w", padding="2 5")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.update_status("Ready. Please select images to convert.")

    def on_orientation_change(self, event=None):
        """Handle orientation change and refresh preview."""
        self.show_preview()

    def browse_images(self):
        """Open file dialog to select multiple images."""
        file_types = [("Image Files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff"), ("All files", "*.*")]
        files = filedialog.askopenfilenames(title="Select Images", filetypes=file_types)
        
        if files:
            for file in files:
                if file not in self.image_paths:
                    self.image_paths.append(file)
            self.update_image_listbox()
            self.image_listbox.selection_set(len(self.image_paths) - 1)
            self.show_preview()

    def update_image_listbox(self):
        """Clears and repopulates the listbox with current image paths."""
        self.image_listbox.delete(0, tk.END)
        for path in self.image_paths:
            # Show just the filename, not the full path
            self.image_listbox.insert(tk.END, os.path.basename(path))
        self.update_status(f"{len(self.image_paths)} images selected.")

    def create_page_preview(self, image, orientation):
        """Create a preview showing how the image will appear on the PDF page."""
        # Define page dimensions (A4)
        if orientation == "Portrait":
            page_width, page_height = 210, 297  # A4 in mm
            self.orientation_info.config(text="Preview: Portrait A4")
        else:
            page_width, page_height = 297, 210  # A4 Landscape in mm
            self.orientation_info.config(text="Preview: Landscape A4")
        
        # Create a canvas representing the PDF page
        canvas_size = 400
        page_aspect = page_width / page_height
        
        if page_aspect > 1:  # Landscape
            canvas_width = canvas_size
            canvas_height = int(canvas_size / page_aspect)
        else:  # Portrait
            canvas_height = canvas_size
            canvas_width = int(canvas_size * page_aspect)
        
        # Create white canvas (representing PDF page)
        page_canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
        draw = ImageDraw.Draw(page_canvas)
        
        # Draw page border
        draw.rectangle([0, 0, canvas_width-1, canvas_height-1], outline='#cccccc', width=2)
        
        # Calculate image dimensions and position (same logic as PDF conversion)
        img_width, img_height = image.size
        img_aspect = img_width / img_height
        page_canvas_aspect = canvas_width / canvas_height
        
        # Scale image to fit page while maintaining aspect ratio (90% of page size)
        margin_factor = 0.9
        if img_aspect > page_canvas_aspect:
            # Image is wider than page -> fit to width
            draw_width = int(canvas_width * margin_factor)
            draw_height = int(draw_width / img_aspect)
        else:
            # Image is taller than page -> fit to height
            draw_height = int(canvas_height * margin_factor)
            draw_width = int(draw_height * img_aspect)
        
        # Center the image on the page
        x_pos = (canvas_width - draw_width) // 2
        y_pos = (canvas_height - draw_height) // 2
        
        # Resize and paste the image onto the canvas
        resized_image = image.resize((draw_width, draw_height), Image.Resampling.LANCZOS)
        page_canvas.paste(resized_image, (x_pos, y_pos))
        
        # Add orientation label in corner
        draw = ImageDraw.Draw(page_canvas)
        orientation_text = f"{orientation}"
        try:
            # Simple text drawing (may not work on all systems)
            draw.text((5, 5), orientation_text, fill='#666666')
        except:
            # Fallback if font rendering fails
            pass
        
        return page_canvas

    def show_preview(self, event=None):
        """Displays the selected image in the preview pane with orientation simulation."""
        selected_indices = self.image_listbox.curselection()
        if not selected_indices:
            return

        selected_index = selected_indices[0]
        image_path = self.image_paths[selected_index]

        try:
            # Open the image
            img = Image.open(image_path)
            
            # Create page preview with current orientation
            current_orientation = self.orientation_var.get()
            page_preview = self.create_page_preview(img, current_orientation)
            
            # Get preview pane dimensions
            preview_width = self.preview_label.winfo_width()
            preview_height = self.preview_label.winfo_height()
            
            if preview_width < 50 or preview_height < 50:  # Widget not yet drawn
                preview_width, preview_height = 400, 400

            # Resize preview for display (maintaining aspect ratio)
            page_preview.thumbnail((preview_width - 10, preview_height - 10), Image.Resampling.LANCZOS)

            # Convert to Tkinter-compatible photo image
            self.preview_image = ImageTk.PhotoImage(page_preview)  # Keep a reference!
            self.preview_label.config(image=self.preview_image, text="")
            
        except Exception as e:
            self.preview_label.config(image="", text=f"Error: Cannot preview\n{os.path.basename(image_path)}\n{e}")
            self.update_status(f"Error previewing image: {e}", error=True)

    def move_up(self):
        """Moves the selected image up in the list."""
        selected_indices = self.image_listbox.curselection()
        if not selected_indices:
            return

        idx = selected_indices[0]
        if idx > 0:
            # Swap in the list of paths
            self.image_paths[idx], self.image_paths[idx-1] = self.image_paths[idx-1], self.image_paths[idx]
            # Update listbox and re-select the moved item
            self.update_image_listbox()
            self.image_listbox.selection_set(idx - 1)
            self.image_listbox.activate(idx - 1)
            self.show_preview()

    def move_down(self):
        """Moves the selected image down in the list."""
        selected_indices = self.image_listbox.curselection()
        if not selected_indices:
            return

        idx = selected_indices[0]
        if idx < len(self.image_paths) - 1:
            self.image_paths[idx], self.image_paths[idx+1] = self.image_paths[idx+1], self.image_paths[idx]
            self.update_image_listbox()
            self.image_listbox.selection_set(idx + 1)
            self.image_listbox.activate(idx + 1)
            self.show_preview()

    def remove_image(self):
        """Removes the selected image from the list."""
        selected_indices = self.image_listbox.curselection()
        if not selected_indices:
            return

        idx = selected_indices[0]
        del self.image_paths[idx]
        self.update_image_listbox()

        # Clear preview if list is empty
        if not self.image_paths:
            self.preview_label.config(image="", text="Image Preview will be shown here")
            self.orientation_info.config(text="Preview: Portrait A4")
        else:
            # Select the next item or the last one
            new_selection = min(idx, len(self.image_paths) - 1)
            if new_selection >= 0:
                self.image_listbox.selection_set(new_selection)
                self.show_preview()

    def convert_to_pdf(self):
        """Converts the list of images to a single PDF file."""
        if not self.image_paths:
            messagebox.showerror("Error", "No images selected. Please browse for images first.")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf")],
            title="Save PDF As..."
        )

        if not output_path:
            self.update_status("PDF conversion cancelled.")
            return

        try:
            self.update_status("Converting to PDF...")
            self.update() # Force GUI update

            # Set page size based on orientation
            page_size = A4
            if self.orientation_var.get() == "Landscape":
                page_size = landscape(A4)
            
            c = canvas.Canvas(output_path, pagesize=page_size)
            page_width, page_height = page_size
            
            for i, image_path in enumerate(self.image_paths):
                self.update_status(f"Processing image {i+1}/{len(self.image_paths)}...")
                self.update()
                
                try:
                    # Open image to get its dimensions
                    img_reader = ImageReader(image_path)
                    img_width, img_height = img_reader.getSize()
                    
                    # Calculate aspect ratios
                    img_aspect = img_width / float(img_height)
                    page_aspect = page_width / float(page_height)
                    
                    # Scale image to fit page while maintaining aspect ratio
                    if img_aspect > page_aspect:
                        # Image is wider than page -> fit to width
                        draw_width = page_width * 0.9 # 90% margin
                        draw_height = draw_width / img_aspect
                    else:
                        # Image is taller than page -> fit to height
                        draw_height = page_height * 0.9 # 90% margin
                        draw_width = draw_height * img_aspect
                        
                    # Center the image on the page
                    x_pos = (page_width - draw_width) / 2
                    y_pos = (page_height - draw_height) / 2

                    c.drawImage(image_path, x_pos, y_pos, width=draw_width, height=draw_height, preserveAspectRatio=True)
                    c.showPage() # Create a new page for the next image
                except Exception as e:
                    print(f"Could not process image {image_path}: {e}")
                    # Optionally, skip the image or show a warning
                    continue
            
            c.save()
            messagebox.showinfo("Success", f"Successfully created PDF!\nSaved to: {output_path}")
            self.update_status(f"PDF saved successfully to {output_path}")

        except Exception as e:
            messagebox.showerror("Conversion Error", f"An error occurred during PDF conversion:\n{e}")
            self.update_status(f"Error during conversion: {e}", error=True)

    def update_status(self, message, error=False):
        """Updates the status bar text and color."""
        self.status_var.set(message)
        if error:
            self.status_bar.config(foreground="red")
        else:
            self.status_bar.config(foreground="black")


if __name__ == "__main__":
    app = ImageToPdfConverter()
    app.mainloop()
