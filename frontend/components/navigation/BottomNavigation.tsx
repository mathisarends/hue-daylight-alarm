import React from 'react';
import { View, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export type NavigationTab = 'home' | 'discover' | 'profile';

interface BottomNavigationProps {
  activeTab: NavigationTab;
  onTabChange: (tab: NavigationTab) => void;
}

export const BottomNavigation: React.FC<BottomNavigationProps> = ({ activeTab, onTabChange }) => {
  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={styles.tab}
        onPress={() => onTabChange('home')}
      >
        <Ionicons
          name={activeTab === 'home' ? 'home' : 'home-outline'}
          size={24}
          color={activeTab === 'home' ? '#000' : '#999'}
        />
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.tab}
        onPress={() => onTabChange('discover')}
      >
        <Ionicons
          name={activeTab === 'discover' ? 'sparkles' : 'sparkles-outline'}
          size={24}
          color={activeTab === 'discover' ? '#000' : '#999'}
        />
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.tab}
        onPress={() => onTabChange('profile')}
      >
        <Ionicons
          name={activeTab === 'profile' ? 'person' : 'person-outline'}
          size={24}
          color={activeTab === 'profile' ? '#000' : '#999'}
        />
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    paddingBottom: 20,
    paddingTop: 12,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
  },
});
