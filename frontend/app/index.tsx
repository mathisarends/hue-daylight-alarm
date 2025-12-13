import React, { useState } from 'react';
import { View, StyleSheet } from 'react-native';
import { HomeScreen } from '../screens/HomeScreen';
import { DiscoverScreen } from '../screens/DiscoverScreen';
import { ProfileScreen } from '../screens/ProfileScreen';
import { BottomNavigation, NavigationTab } from '../components/navigation/BottomNavigation';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavigationTab>('home');

  const renderScreen = () => {
    switch (activeTab) {
      case 'home':
        return <HomeScreen />;
      case 'discover':
        return <DiscoverScreen />;
      case 'profile':
        return <ProfileScreen />;
      default:
        return <HomeScreen />;
    }
  };

  return (
    <View style={styles.container}>
      {renderScreen()}
      <BottomNavigation activeTab={activeTab} onTabChange={setActiveTab} />
    </View>
  );
};

export default App;

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
});
