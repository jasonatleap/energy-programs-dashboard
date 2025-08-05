# US Energy Incentive Programs Dashboard

An interactive heat map visualization showing energy incentive programs across the United States, with filtering capabilities by device type and region.

## Features

- **Interactive Heat Map**: Visual representation of program density by state
- **Device Type Filtering**: Filter programs by:
  - EV Chargers
  - HVAC Systems
  - Smart Thermostats
  - Solar Storage
  - Water Heaters
  - Weatherization
- **Regional Filtering**: Filter by US regions:
  - Southwest
  - West
  - Southeast
  - Midwest
  - Mid-Atlantic
  - Northeast
- **Real-time Statistics**: View program counts and breakdowns
- **Hover Information**: See detailed regional statistics on hover

## Setup

### Prerequisites

- Python 3.9+
- Supabase account with access to programs data

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd energy-programs-dashboard
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-anon-key"
```

Or create a `.env` file:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

### Running Locally

```bash
python app.py
```

The dashboard will be available at `http://localhost:8050`

## Deployment

### Deploy to Render

1. Fork this repository
2. Connect your GitHub account to Render
3. Create a new Web Service
4. Select this repository
5. Add environment variables:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
6. Deploy!

### Deploy to Heroku

1. Create a `Procfile`:
```
web: gunicorn app:server
```

2. Deploy:
```bash
heroku create your-app-name
heroku config:set SUPABASE_URL="your-url"
heroku config:set SUPABASE_KEY="your-key"
git push heroku main
```

### Deploy to Railway

1. Connect your GitHub repository
2. Add environment variables in Railway dashboard
3. Deploy automatically

## Data Structure

The dashboard expects the following Supabase tables:

- **programs**: Contains program information with columns:
  - `state_province` (2-letter state code)
  - `device_category_id` (foreign key to device_categories)
  
- **device_categories**: Contains device type information with columns:
  - `id` (primary key)
  - `name` (device type name)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Dash](https://dash.plotly.com/) and [Plotly](https://plotly.com/)
- Data powered by [Supabase](https://supabase.com/)
- Map visualization using US state boundaries