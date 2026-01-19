# HopeFund FastAPI Server

This is the FastAPI version of the HopeFund server, converted from the original Express.js server.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the `server-fast` directory with the following variables:
```
DB_URL=your_mongodb_connection_string
REDIS_URL=your_redis_connection_string
ACCESS_TOKEN=your_access_token_secret
REFRESH_TOKEN=your_refresh_token_secret
ACTIVATION_SECRET=your_activation_secret
CLOUD_NAME=your_cloudinary_cloud_name
CLOUD_API_KEY=your_cloudinary_api_key
CLOUD_SECRET_KEY=your_cloudinary_secret_key
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
SMTP_HOST=your_smtp_host
SMTP_PORT=587
SMTP_SERVICE=your_smtp_service
SMTP_MAIL=your_smtp_email
SMTP_PASSWORD=your_smtp_password
PORT=8000
```

3. Run the server:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --port 8000
```

## API Endpoints

All endpoints are prefixed with `/api/v1/`

### User Routes
- `POST /registration` - Register a new user
- `POST /activate-user` - Activate user account
- `POST /login` - Login user
- `GET /logout` - Logout user
- `GET /refresh` - Refresh access token
- `GET /me` - Get current user info
- `POST /socialAuth` - Social authentication
- `PUT /update-user-info` - Update user info
- `PUT /update-user-avatar` - Update user avatar
- `PUT /update-user-fundArray` - Update user fund array
- `GET /getUser` - Get user by email
- `POST /get-user-pic` - Get user picture

### Fundraiser Routes
- `POST /createFundraiser` - Create a fundraiser
- `PUT /edit-fund/{id}` - Edit fundraiser
- `PUT /update-fund-amount/{id}` - Update fundraiser amount
- `GET /getAllFunds` - Get all fundraisers
- `GET /getAllFundsByUrgency` - Get fundraisers by urgency
- `GET /get-fund/{id}` - Get single fundraiser
- `GET /getUserCreatedFunds` - Get user's created funds
- `GET /getUserDonatedFunds` - Get user's donated funds
- `POST /addBenefitterImg` - Add benefitter image
- `POST /deleteBenefitterImg` - Delete benefitter image
- `POST /addCoverImg` - Add cover image
- `POST /deleteCoverImg` - Delete cover image
- `POST /fundraiserByType` - Get fundraisers by type
- `POST /fundraiserBySearch` - Search fundraisers

### Contact Routes
- `POST /contact` - Submit contact form

### Payment Routes
- `POST /make-payment` - Process payment
- `GET /payment/stripepublishablekey` - Get Stripe publishable key
- `POST /payment` - Create payment intent

## Features

- FastAPI with async/await support
- MongoDB with Motor (async driver)
- Redis for caching
- JWT authentication
- Cloudinary for image uploads
- Stripe for payments
- Email sending with Jinja2 templates
- Rate limiting
- CORS support
- Error handling middleware

