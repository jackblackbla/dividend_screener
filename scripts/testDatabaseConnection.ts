import { AppDataSource } from '../infrastructure/config/database.config';

async function testDatabaseConnection() {
  try {
    await AppDataSource.initialize();
    console.log('Database connection successful!');
    await AppDataSource.destroy();
  } catch (error) {
    console.error('Database connection failed:', error);
  }
}

testDatabaseConnection();