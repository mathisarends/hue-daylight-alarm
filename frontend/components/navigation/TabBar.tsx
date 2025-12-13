import React from 'react';
import { View, TouchableOpacity, Text, StyleSheet } from 'react-native';

interface Tab {
  label: string;
  value: string;
}

interface TabBarProps {
  tabs: Tab[];
  activeTab: string;
  onTabChange: (value: string) => void;
}

export const TabBar: React.FC<TabBarProps> = ({ tabs, activeTab, onTabChange }) => {
  return (
    <View style={styles.container}>
      {tabs.map((tab) => (
        <TouchableOpacity
          key={tab.value}
          style={[
            styles.tab,
            activeTab === tab.value && styles.tabActive
          ]}
          onPress={() => onTabChange(tab.value)}
        >
          <Text
            style={[
              styles.tabText,
              activeTab === tab.value && styles.tabTextActive
            ]}
          >
            {tab.label}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabActive: {
    borderBottomColor: '#000',
  },
  tabText: {
    fontSize: 16,
    color: '#999',
  },
  tabTextActive: {
    color: '#000',
    fontWeight: '600',
  },
});
