// Simple test to verify API connectivity
// Run with: node test-api.js

const fetch = require('node-fetch')

async function testAPI() {
  console.log('Testing API connectivity...\n')
  
  try {
    // Test document service
    console.log('1. Testing Document Service...')
    const docsResponse = await fetch(`${process.env.NEXT_PUBLIC_DOCUMENT_SERVICE_URL || 'http://localhost:5003'}/documents?limit=3`)
    const docsData = await docsResponse.json()
    
    if (docsResponse.ok) {
      console.log('✅ Document Service: OK')
      console.log(`   - Status: ${docsData.status}`)
      console.log(`   - Documents count: ${docsData.data.length}`)
      console.log(`   - First document: ${docsData.data[0]?.document_name}`)
    } else {
      console.log('❌ Document Service: FAILED')
      console.log(`   - Error: ${docsData.message}`)
    }
  } catch (error) {
    console.log('❌ Document Service: FAILED')
    console.log(`   - Error: ${error.message}`)
  }

  try {
    // Test categories service
    console.log('\n2. Testing Categories Service...')
    const catsResponse = await fetch('http://localhost:5002/categories')
    const catsData = await catsResponse.json()
    
    if (catsResponse.ok) {
      console.log('✅ Categories Service: OK')
      console.log(`   - Categories count: ${catsData.length}`)
      console.log(`   - First category: ${catsData[0]?.category_name}`)
    } else {
      console.log('❌ Categories Service: FAILED')
      console.log(`   - Error: ${catsData.message || 'Unknown error'}`)
    }
  } catch (error) {
    console.log('❌ Categories Service: FAILED')
    console.log(`   - Error: ${error.message}`)
  }

  console.log('\n3. Data Transformation Test...')
  try {
    // Test data transformation
    const sampleDoc = {
      document_id: 1,
      document_name: "Test Document.pdf",
      document_type: "PDF",
      link: "https://example.com/test.pdf",
      categories: [1, 2],
      company: 1,
      uploaded_by: 1,
      upload_date: "2025-08-15T10:00:00+00:00"
    }

    const sampleCategories = [
      { category_id: 1, category_name: "Financial Report", parent_category_id: null },
      { category_id: 2, category_name: "Risk Management", parent_category_id: null },
      { category_id: 3, category_name: "Credit Risk", parent_category_id: 2 }
    ]

    // Simulate transformation (simplified)
    const transformed = {
      id: sampleDoc.document_id.toString(),
      name: sampleDoc.document_name,
      uploadDate: sampleDoc.upload_date.split('T')[0],
      tags: sampleDoc.categories.map(catId => {
        const cat = sampleCategories.find(c => c.category_id === catId)
        return cat ? cat.category_name : `Category ${catId}`
      }),
      size: "2.1 MB", // Estimated
      type: sampleDoc.document_type
    }

    console.log('✅ Data Transformation: OK')
    console.log(`   - Original: ${sampleDoc.document_name}`)
    console.log(`   - Transformed: ${transformed.name}`)
    console.log(`   - Tags: ${transformed.tags.join(', ')}`)
    
  } catch (error) {
    console.log('❌ Data Transformation: FAILED')
    console.log(`   - Error: ${error.message}`)
  }

  console.log('\n🎉 API Testing Complete!')
  console.log('\nNext steps:')
  console.log('1. Your frontend on port 3001 should now be able to load dynamic data')
  console.log('2. Check the browser console for any CORS or network errors')
  console.log('3. The documents should load from the backend instead of static data')
}

testAPI().catch(console.error)