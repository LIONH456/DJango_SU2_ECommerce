# Fashion E-Commerce Django Project

A modern e-commerce website built with Django, featuring a beautiful UI based on the Shionhouse template.

## Features

- **Responsive Design**: Modern, mobile-friendly interface
- **User Authentication**: Login, registration, and profile management
- **Product Management**: Product listing, details, and shopping cart
- **Blog System**: Blog posts with categories and tags
- **Admin Dashboard**: Custom admin interface for managing the store
- **Contact Forms**: Customer support and inquiry forms

## Template Structure

```
templates/
├── base.html           # Base template (all pages inherit this)
├── includes/           # Include fragments
│   ├── header.html     # Site header with navigation
│   ├── footer.html     # Site footer
│   ├── navigation.html # Secondary navigation
│   └── scripts.html    # JavaScript includes
├── Home/               # Home module templates
│   ├── index.html      # Homepage
│   ├── about.html      # About page
│   ├── blog.html       # Blog listing
│   ├── blog_details.html # Individual blog posts
│   ├── contact.html    # Contact page
│   └── elements.html   # UI elements showcase
├── store/              # Store module templates
│   ├── product_list.html   # Product listing
│   ├── product_detail.html # Product details
│   └── cart.html          # Shopping cart
├── auth/               # Authentication templates
│   ├── login.html      # Login form
│   ├── register.html   # Registration form
│   └── profile.html    # User profile
└── admin/              # Admin templates
    └── custom_dashboard.html # Custom admin dashboard
```

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repository-url>
cd ECommerce
```

### 2. Create Virtual Environment
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 6. Run the Development Server
```bash
python manage.py runserver
```

### 7. Access the Website
- Main site: http://127.0.0.1:8000/
- Admin panel: http://127.0.0.1:8000/admin/

## Project Structure

```
ECommerce/
├── ECommerce/          # Project settings
│   ├── settings.py     # Django settings
│   ├── urls.py         # Main URL configuration
│   └── wsgi.py         # WSGI configuration
├── main/               # Main application
│   ├── views.py        # View functions
│   ├── urls.py         # App URL configuration
│   ├── models.py       # Database models
│   └── admin.py        # Admin configuration
├── templates/          # HTML templates
├── shionhouse-master/  # Static assets (CSS, JS, images)
├── manage.py           # Django management script
└── requirements.txt    # Python dependencies
```

## Static Files

The project uses the Shionhouse template assets located in `shionhouse-master/assets/`. These include:
- CSS files for styling
- JavaScript files for interactivity
- Image files for the design
- Font files for typography

## Customization

### Adding New Pages
1. Create a new template in the appropriate directory
2. Add a view function in `main/views.py`
3. Add a URL pattern in `main/urls.py`
4. Update navigation in `templates/includes/header.html`

### Styling
- Main styles are in `shionhouse-master/assets/css/style.css`
- Custom styles can be added in template-specific `<style>` blocks
- Bootstrap 4 classes are available for layout and components

### JavaScript
- jQuery and Bootstrap JS are included
- Custom JavaScript can be added in template-specific `<script>` blocks
- AJAX functionality is available for dynamic interactions

## Development Notes

- The project is configured for development with `DEBUG = True`
- Static files are served from the `shionhouse-master/assets/` directory
- Media files will be stored in a `media/` directory when implemented
- Database is SQLite by default (can be changed in settings.py)

## Future Enhancements

- Product database models
- Shopping cart functionality
- Payment gateway integration
- User reviews and ratings
- Order management system
- Email notifications
- Search functionality
- Filtering and sorting
- Wishlist feature
- Social media integration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational purposes. The Shionhouse template assets are subject to their respective licenses.

## Support

For questions or support, please open an issue in the repository.
